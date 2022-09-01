#
# os/fs.py
#


"""Interfaces to filesystem and related tools.
"""


import os
import os.path
import subprocess


class Mounter:
    """Mount and unmount filesystems.
    """

    @staticmethod
    def mount(path):
        """Mount filesystem at path as listed in /etc/fstab.

        Args:
            path: Path at which filesystem should be mounted.
        """

        try:
            os.makedirs(path)
        except:
            pass
        if os.path.isdir(path):
            p = subprocess.run(["mount", path])

    @staticmethod
    def umount(path):
        """Unmount filesystem at path.

        Args:
            path: Path at which filesystem is mounted.
        """

        p = subprocess.run(["umount", path])
