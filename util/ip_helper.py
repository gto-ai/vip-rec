import subprocess
import re


class IPHelper:
    @classmethod
    def get_network_interface(cls, ip_pattern: str) -> str | None:
        """
        ip_pattern example: '192.168.31.*'
        """
        # convert wildcard pattern to regex
        ip_regex = ip_pattern.replace('.', r'\.').replace('*', r'\d+')

        result = subprocess.run(
            ["ifconfig"],
            capture_output=True,
            text=True,
            check=True,
        )

        blocks = result.stdout.split("\n\n")

        for block in blocks:
            if re.search(rf"\binet {ip_regex}\b", block):
                # interface name is before the first colon
                return block.split(":")[0]

        return None

    @classmethod
    def get_username(cls):
        username = subprocess.check_output(["whoami"], text=True).strip()
        return username


def main():
    iface = IPHelper.get_network_interface("192.168.31.*")
    print(iface)


if __name__ == "__main__":
    main()
