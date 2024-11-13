from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("VERSION", "r") as fh:
    version = fh.read()

setup(
    name="netbox_kea_updater",
    version=version,
    author="Simon Rance",
    author_email="sirance@gmail.com",
    description="Read leases from Kea DHCP4 API, and add to netbox IPAM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sirance/netbox-kea-updater",
    packages=['netbox_kea_updater'],
        entry_points={
        'console_scripts': [
            'netbox_kea_updater=netbox_kea_updater.netbox_kea_updater:cli'
        ]
    },
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'click~=8.1',
        'pykeadhcp~=0.6.0',
        'pynetbox~=7.4',
            ],
    package_data={
    },
    zip_safe=False
)
