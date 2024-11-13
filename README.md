# netbox_kea_updater

Reads DHCP leases from Kea's api, and checks against netbox IPAM.

It will create IP addresses if they don't exist, and add lease time & HW address info into custom fields. (details below)

## Installation

It is recommended to use a python virtual environment.

To install simply run:

```bash
pip3 install .
```

or

```bash
python3 -m pip install .
```

This should install all dependancies into the virtualenv.

### Usage

The script is run as follows:

```bash
netbox_kea_updater --verbose processleases --netbox-url --netbox-token --kea-url --remove-old
```

### Parameters

The parameters used in this script are as follows:

| Parameter | Environment Variable | Description | Required |
|----|-----|------|------|
| --netbox-url | NETBOX_URL | The full URL for netbox API | yes |
| --netbox-token | NETBOX_TOKEN | An api token for netbox, with appropiate IPAM permissions | yes |
| --kea-url | KEA_URL | The full URL for Kea API | yes |
| --kea-port | KEA_URL | The port number for Kea API | yes |
| --(no-)verbose | | Enable versbose mode in the script | no |
| --(no-)-netbox-dns-manage | | Whether to allow Netbox DNS plugin to manage record | no (defaults to manage) |
| --(no-)remove-old | | Whether to remove IP Addresses from netbox, if a lease no longer exists for it.| no (defaults to not removing) |

## Netbox custom field requirements

This code looks for two (optionally three) custom fields as below:

* **dhcp_lease**: Text type, Content type: **IPAM** > **IP Address**

* **dhcp_hwaddress**: Text type, Content type: **IPAM** > **IP Address**

* **disable_ip_manage**: This is only used with netbox DNS plugin, when the plugin is running this field is available.
