# Copyright 2022 The Kraken Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import tempfile

import distro

from kraken.agent import utils


log = logging.getLogger(__name__)


def run(step, **kwargs):  # pylint: disable=unused-argument
    pkgs = step['pkgs']

    if not pkgs:
        log.info('no packages to install')
        return

    system = distro.id()
    sys_ver = distro.version()

    if not isinstance(pkgs, list):
        pkgs = pkgs.split(',')
        pkgs = [p.strip() for p in pkgs]
        pkgs2 = []
        for p in pkgs:
            pkgs2.extend(p.split())
        pkgs = pkgs2

    env = None

    provider = step.get('provider', None)

    if provider is None:
        if system in ['centos', 'rhel'] and sys_ver == '7':
            provider = 'yum'
        elif system == 'fedora' or (system in ['centos', 'rhel'] and sys_ver == '8'):
            provider = 'dnf'
        elif system in ['debian', 'ubuntu']:
            provider = 'apt'
        elif system == 'freebsd':
            provider = 'pkg'
        elif system == 'alpine':
            provider = 'apk'
        elif system == 'arch':
            provider = 'pacman'
        else:
            raise NotImplementedError('no implementation for %s' % system)

    if provider == 'yum':
        # skip_missing_names_on_install used to detect case when one packet is not found and no error is returned
        # but we want an error
        cmd = 'sudo yum install -y --setopt=skip_missing_names_on_install=False'
    elif provider == 'dnf':
        cmd = 'sudo dnf -y install'
    elif provider == 'apt':
        if not env:
            env = os.environ.copy()
        env['DEBIAN_FRONTEND'] = 'noninteractive'
        cmd = 'sudo apt install --no-install-recommends -y'
    elif provider == 'pkg':
        cmd = 'sudo pkg install -y'
    elif provider == 'apk':
        cmd = 'sudo apk add'
    elif provider == 'pacman':
        cmd = 'sudo pacman -S --needed --noconfirm --overwrite \'*\''

    timeout = step.get('timeout', 60)

    pkgs = ' '.join(pkgs)
    cmd += ' ' + pkgs
    ret = utils.execute(cmd, timeout=timeout, env=env, ignore_output=True)

    if ret != 0:
        result = [ret, 'cmd exited with non-zero retcode: %s' % ret]
    else:
        result = [0, '']

    return result


def main():
    logging.basicConfig(level=logging.INFO)
    step = dict(pkgs='mc')
    run(step)


if __name__ == '__main__':
    main()
