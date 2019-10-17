# -*- coding: UTF-8 -*-

import os
import json
import six
import mock
import pytest
import yaml
from .helpers import insights_upload_conf
from mock.mock import patch
from insights.client.collection_rules import InsightsUploadConf
from insights.client.config import InsightsConfig


conf_remove_file = '/tmp/remove.conf'
removed_files = ["/etc/some_file", "/tmp/another_file"]


def teardown_function(func):
    if func is test_raw_config_parser:
        if os.path.isfile(conf_remove_file):
            os.remove(conf_remove_file)


def patch_isfile(isfile):
    """
    Makes isfile return the passed result.
    """
    def decorator(old_function):
        patcher = patch("insights.client.collection_rules.os.path.isfile", return_value=isfile)
        return patcher(old_function)
    return decorator


def patch_raw_config_parser(items):
    """
    Mocks RawConfigParser so it returns the passed items.
    """
    def decorator(old_function):
        patcher = patch("insights.client.collection_rules.ConfigParser.RawConfigParser",
                          **{"return_value.items.return_value": items})
        return patcher(old_function)
    return decorator


def patch_open():
    if six.PY3:
        open_name = 'builtins.open'
    else:
        open_name = '__builtin__.open'

    return patch(open_name, create=True)


@patch_raw_config_parser([])
@patch_isfile(False)
def test_no_file(isfile, raw_config_parser):
    upload_conf = insights_upload_conf(remove_file=conf_remove_file)
    result = upload_conf.get_rm_conf()

    isfile.assert_called_once_with(conf_remove_file)

    # no file, no call to open
    with patch_open() as mock_open:
        mock_open.assert_not_called()

    assert result is None


@patch('insights.client.collection_rules.InsightsUploadConf.get_rm_conf_old')
@patch_isfile(True)
def test_return(isfile, get_rm_conf_old):
    '''
    Test that loading YAML from a file will return a dict
    '''
    filedata = '---\ncommands:\n- /bin/ls\n- ethtool_i'
    with patch_open() as mock_open:
        mock_open.side_effect = [mock.mock_open(read_data=filedata).return_value]
        upload_conf = insights_upload_conf(remove_file=conf_remove_file)
        result = upload_conf.get_rm_conf()
    assert result == {'commands': ['/bin/ls', 'ethtool_i']}
    get_rm_conf_old.assert_not_called()


@patch('insights.client.collection_rules.InsightsUploadConf.get_rm_conf_old')
@patch_isfile(True)
def test_fallback_to_old(isfile, get_rm_conf_old):
    '''
    Test that the YAML function falls back to classic INI
    if the file cannot be parsed as YAML
    '''
    filedata = 'ncommands\n /badwain/ls\n- ethtool_i'
    with patch_open() as mock_open:
        mock_open.side_effect = [mock.mock_open(read_data=filedata).return_value]
        upload_conf = insights_upload_conf(remove_file=conf_remove_file)
        result = upload_conf.get_rm_conf()
    get_rm_conf_old.assert_called_once()


@patch_isfile(True)
def test_fallback_ini_data(isfile):
    '''
    Test that the YAML function falls back to classic INI
    if the file cannot be parsed as YAML, and the data is
    parsed as INI
    '''
    filedata = '[remove]\ncommands=/bin/ls,ethtool_i'
    with patch_open() as mock_open:
        # need two since the file will be open()'d twice'
        mock_open.side_effect = [mock.mock_open(read_data=filedata).return_value,
                                 mock.mock_open(read_data=filedata).return_value]
        upload_conf = insights_upload_conf(remove_file=conf_remove_file)
        result = upload_conf.get_rm_conf()
    assert result == {'commands': ['/bin/ls', 'ethtool_i']}


@patch_isfile(True)
def test_fallback_bad_data(isfile):
    '''
    Test that the YAML function falls back to classic INI
    if the file cannot be parsed as YAML, and the data isn't
    INI either so it's thrown out
    '''
    return
    filedata = 'ncommands\n /badwain/ls\n- ethtool_i'
    with patch_open() as mock_open:
        # need two since the file will be open()'d twice'
        mock_open.side_effect = [mock.mock_open(read_data=filedata).return_value,
                                 mock.mock_open(read_data=filedata).return_value]
        upload_conf = insights_upload_conf(remove_file=conf_remove_file)
        result = upload_conf.get_rm_conf()
    assert result is None


@patch_raw_config_parser([("files", ",".join(removed_files))])
@patch_isfile(True)
def test_return_old(isfile, raw_config_parser):
    upload_conf = insights_upload_conf(remove_file=conf_remove_file)
    result = upload_conf.get_rm_conf_old()

    raw_config_parser.assert_called_once_with()
    raw_config_parser.return_value.read.assert_called_with(conf_remove_file)
    raw_config_parser.return_value.items.assert_called_with('remove')

    assert result == {"files": removed_files}


def test_raw_config_parser():
    '''
        Ensure that get_rm_conf and json.loads (used to load uploader.json) return the same filename
    '''
    raw_filename = '/etc/yum/pluginconf.d/()*\\\\w+\\\\.conf'
    uploader_snip = json.loads('{"pattern": [], "symbolic_name": "pluginconf_d", "file": "' + raw_filename + '"}')
    with open(conf_remove_file, 'w') as rm_conf:
        rm_conf.write('[remove]\nfiles=' + raw_filename)
    coll = InsightsUploadConf(InsightsConfig(remove_file=conf_remove_file))
    items = coll.get_rm_conf()
    assert items['files'][0] == uploader_snip['file']
