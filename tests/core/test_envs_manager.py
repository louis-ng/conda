# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from logging import getLogger
import os
from os.path import isdir, join, lexists
from tempfile import gettempdir
from unittest import TestCase
from uuid import uuid4

from conda._vendor.auxlib.collection import AttrDict
from conda.base.constants import PREFIX_MAGIC_FILE
from conda.base.context import context, reset_context
from conda.common.io import env_var
from conda.common.path import paths_equal
from conda.core.envs_manager import list_all_known_prefixes, register_env, USER_ENVIRONMENTS_TXT_FILE, \
    unregister_env
from conda.gateways.disk import mkdir_p
from conda.gateways.disk.delete import rm_rf
from conda.gateways.disk.read import yield_lines
from conda.gateways.disk.update import touch

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

log = getLogger(__name__)


class EnvsManagerUnitTests(TestCase):

    def setUp(self):
        tempdirdir = gettempdir()
        dirname = str(uuid4())[:8]
        self.prefix = join(tempdirdir, dirname)
        mkdir_p(self.prefix)
        assert isdir(self.prefix)

    def tearDown(self):
        rm_rf(self.prefix)
        assert not lexists(self.prefix)

    def test_register_unregister_location_env(self):
        gascon_location = join(self.prefix, 'gascon')
        touch(join(gascon_location, PREFIX_MAGIC_FILE), mkdir=True)
        assert gascon_location not in list_all_known_prefixes()

        touch(USER_ENVIRONMENTS_TXT_FILE, mkdir=True, sudo_safe=True)
        register_env(gascon_location)
        assert gascon_location in yield_lines(USER_ENVIRONMENTS_TXT_FILE)
        assert len(tuple(x for x in yield_lines(USER_ENVIRONMENTS_TXT_FILE) if paths_equal(gascon_location, x))) == 1

        register_env(gascon_location)  # should be completely idempotent
        assert len(tuple(x for x in yield_lines(USER_ENVIRONMENTS_TXT_FILE) if x == gascon_location)) == 1

        unregister_env(gascon_location)
        assert gascon_location not in list_all_known_prefixes()
        unregister_env(gascon_location)  # should be idempotent
        assert gascon_location not in list_all_known_prefixes()

    def test_prefix_cli_flag(self):
        envs_dirs = (join(self.prefix, 'first-envs-dir'), join(self.prefix, 'seconds-envs-dir'))
        with env_var('CONDA_ENVS_DIRS', os.pathsep.join(envs_dirs), reset_context):

            # even if prefix doesn't exist, it can be a target prefix
            reset_context((), argparse_args=AttrDict(prefix='./blarg', func='create'))
            target_prefix = join(os.getcwd(), 'blarg')
            assert context.target_prefix == target_prefix
            assert not isdir(target_prefix)
