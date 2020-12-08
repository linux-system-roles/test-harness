#!/usr/bin/python3


import sys
import yaml

DISTROS = {"fedora": "Fedora", "rhel": "EL", "centos": "EL"}


def distro_to_platform(distro):
    """convert distro (ID from os-release(5)) to platform used in role meta"""
    return DISTROS.get(distro, distro)


def role_supported_versions(metafile, distro):
    """return a list of distribution versions that role's metadata claim to support"""
    with open(metafile, "r", encoding="utf8") as file:
        meta = yaml.safe_load(file)
        distinfo = next(
            (
                item
                for item in meta["galaxy_info"]["platforms"]
                if item["name"] == distro_to_platform(distro)
            ),
            None,
        )
    if not distinfo:
        return []
    return distinfo["versions"]


def version_match(version, meta_version):
    # could do more complicated matching, but for now assume that
    # meta_version is just a major version (single integer number) or wildcard
    return meta_version == "all" or version == str(meta_version)


def role_supported(metafile, distro, version):
    return any(
        (
            version_match(version, meta_version)
            for meta_version in role_supported_versions(metafile, distro)
        )
    )


if __name__ == "__main__":
    USAGE = (
        f"Usage: { sys.argv[0] } <rolepath>/meta/main.yml distribution [majorversion]"
    )

    # sanity-check arguments
    if len(sys.argv) not in (3, 4):
        print("Invalid arguments.")
        print(USAGE)
        sys.exit(2)
    if len(sys.argv) == 3:
        print(role_supported_versions(sys.argv[1], sys.argv[2]))
        sys.exit(0)
    else:
        sys.exit(not role_supported(sys.argv[1], sys.argv[2], sys.argv[3]))
