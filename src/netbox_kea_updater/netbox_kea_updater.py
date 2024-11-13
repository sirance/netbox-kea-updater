from datetime import datetime
from pykeadhcp import Kea
from pykeadhcp.parsers.dhcp4 import Dhcp4Parser
import pynetbox
import click

#############################################
# CLI Commands
#############################################


@click.group()
@click.option('--verbose/--no-verbose',
              help='enable/disable verbose mode',
              default=False)
@click.pass_context
def cli(ctx=None, verbose=None):
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose


@cli.command()
@click.option('--netbox-url', envvar='NETBOX_API',
              help='URL for accessing netbox api', required=True)
@click.option('--netbox-token', envvar='NETBOX_TOKEN',
              help='API TOKEN for accessing netbox', required=True)
@click.option('--kea-url', envvar='KEA_URL',
              help='URL for accessing KEA DHCP4 API', required=True)
@click.option('--kea-port', envvar='KEA_PORT',
              help='PORT for accessing KEA DHCP4 API', required=True)
@click.option('--netbox-dns-manage/--no-netbox-dns-manage',
              help='Whether to allow Netbox DNS plugin to manage record',
              default=True, required=False)
@click.option('--remove-old/--no-remove-old',
              help='Remove IP from netbox when there is no longer a lease',
              default=False, required=False)
@click.pass_context
def processleases(ctx, netbox_url, netbox_token, kea_url, kea_port, netbox_dns_manage, remove_old):
    # Connect to NetBox
    nb = pynetbox.api(
            netbox_url,
            token=netbox_token
    )

    # Connect to the Kea Agent endpoint
    server = Kea(host=kea_url, port=kea_port)

    format_string = "%Y-%m-%d %H:%M:%S"
    kea_ips = []

    # Check whether to allow Netbox DNS plugin to manage records for IP addresses
    netbox_status = nb.status()
    lease_cltt = ""
    # First check is whether we even have netbox dns plugin running:
    if "netbox_dns" in netbox_status['plugins']:
        print("netbox_dns plugin found")
        # netbox_dns plugin is running, so now check the input variable
        if netbox_dns_manage:
            if ctx.obj['VERBOSE']:
                print("allowing netbox DNS to manage record")
            custom_fields = {'dhcp_lease': str(lease_cltt),
                            'dhcp_hwaddress':
                            str(lease.hw_address.upper()), 
                            'disable_ip_manage': False
                            }
        else:
            if ctx.obj['VERBOSE']:
                print("netbox DNS record management disabled")
            custom_fields = {'dhcp_lease': str(lease_cltt),
                            'dhcp_hwaddress':
                            str(lease.hw_address.upper()), 
                            'disable_ip_manage': True
                            }
    else:
        # netbox dns plugins was not found, so not including the custom field
        if ctx.obj['VERBOSE']:
            print("netbox DNS plugin not found, ignoring options")
        custom_fields = {'dhcp_lease': str(lease_cltt),
                        'dhcp_hwaddress':
                        str(lease.hw_address.upper())
                        }

    # Read current leases from Kea DHCP
    if ctx.obj['VERBOSE']:
        print("Starting check...")
        print("Updating lease information from Kea DHCP into NetBox")
    kea_leases = server.dhcp4.lease4_get_all()

    # Loop through leases, and check for existence in netbox, if not create,
    # else update lease time, if changed.
    for lease in kea_leases:
        kea_ips.append(lease.ip_address)
        leasetime = lease.cltt
        lease_cltt = datetime.fromtimestamp(leasetime)
        if ctx.obj['VERBOSE']:
            print('Lease for {}: valid until {} UTC'
                  .format(lease.ip_address, lease_cltt))
        parser = Dhcp4Parser(config=server.dhcp4.cached_config)
        kea_subnet = parser.get_subnet(id=lease.subnet_id)
        subnet = kea_subnet.subnet.split('/')[-1]
        prefix = nb.ipam.prefixes.get(prefix=kea_subnet.subnet)
        ip_prefixed = lease.ip_address + '/' + subnet
        try:
            nb_ip_address = nb.ipam.ip_addresses.get(address=lease.ip_address)
            if nb_ip_address is None:
                if ctx.obj['VERBOSE']:
                    print(f"IP address: {lease.ip_address} "
                          "missing from netbox, adding...")
                nb.ipam.ip_addresses.create(
                    address=ip_prefixed,
                    description="Added from Kea DHCP",
                    vrf=prefix.vrf.id,
                    dns_name=lease.hostname,
                    custom_fields=custom_fields,
                    status='dhcp'
                )
            else:

                if ctx.obj['VERBOSE']:
                    print(nb_ip_address.custom_fields['dhcp_lease'])
                    print(lease_cltt)
                if nb_ip_address.custom_fields['dhcp_lease'] is None:
                    nb_datetime = "0"
                else:
                    nb_datetime = datetime.strptime(
                        nb_ip_address.custom_fields['dhcp_lease'],
                        format_string)
                if nb_datetime != lease_cltt:
                    if ctx.obj['VERBOSE']:
                        print("Lease times differ updating netbox")
                    nb.ipam.ip_addresses.update([{
                        'id': nb_ip_address.id,
                        'address': nb_ip_address.address,
                        'description': 'Updated from Kea DHCP',
                        'dns_name': lease.hostname,
                        'custom_fields': custom_fields,
                        'status': 'dhcp'
                    }])
                else:
                    if ctx.obj['VERBOSE']:
                        print("Lease times match, not updating")
        except pynetbox.RequestError as e:
            print(e.error)

    # Clear old leases from netbox
    if remove_old:
        if ctx.obj['VERBOSE']:
            print("checking netbox for released IP addresses")
        nb_ips = nb.ipam.ip_addresses.filter(status="dhcp")
        for i in nb_ips:
            nb_ip = i.address.split('/')[0]
            if nb_ip not in kea_ips:
                if ctx.obj['VERBOSE']:
                    print(f"IP address: {nb_ip}"
                          "no longer leased removing from netbox.")
                x = nb.ipam.ip_addresses.get(address=i.address)
                try:
                    x.delete()
                    if ctx.obj['VERBOSE']:
                        print(f"deleted ip record: {x}")
                except pynetbox.RequestError as e:
                    print(e.error)
        if ctx.obj['VERBOSE']:
            print("Completing check...")


#############################################
# Main
#############################################
if __name__ == '__main__':
    cli()
