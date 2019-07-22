
__author__ = 'pcuzner@redhat.com'

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser
from distutils.util import strtobool

import hashlib
import json
import logging
import re


# this module when imported preserves the global values
# defined by the init method allowing other classes to
# access common configuration settings
def init():
    global config
    config = Settings()


class Settings(object):
    LIO_YES_NO_SETTINGS = ["immediate_data", "initial_r2t"]

    LIO_INT_SETTINGS_LIMITS = {
        "cmdsn_depth": {
            "min": 1, "max": 512},
        "dataout_timeout": {
            "min": 2, "max": 60},
        "nopin_response_timeout": {
            "min": 3, "max": 60},
        "nopin_timeout": {
            "min": 3, "max": 60},
        "first_burst_length": {
            "min": 512, "max": 16777215},
        "max_burst_length": {
            "min": 512, "max": 16777215},
        "max_outstanding_r2t": {
            "min": 1, "max": 65535},
        "max_recv_data_segment_length": {
            "min": 512, "max": 16777215},
        "max_xmit_data_segment_length": {
            "min": 512, "max": 16777215},

        "qfull_timeout": {
            "min": 0, "max": 600},
        "hw_max_sectors": {
            "min": 1, "max": 8192},
        "max_data_area_mb": {
            "min": 1, "max": 2048},
        "osd_op_timeout": {
            "min": 0, "max": 600}
    }

    _float_regex = re.compile(r"^[0-9]*\.{1}[0-9]$")
    _int_regex = re.compile(r"^[0-9]+$")

    @staticmethod
    def normalize_controls(raw_controls, settings_list):
        """
        Convert a controls dictionary from a json converted or a user input
        dictionary where the values are strings.
        """
        controls = {}

        for key, raw_value in raw_controls.items():
            if key not in settings_list:
                raise ValueError("Supported controls: {}".format(",".join(settings_list)))

            if raw_value in [None, '']:
                # Use the default/reset.
                controls[key] = None
                continue

            # Do not use normalize() because if the user inputs invalid
            # values we want to pass up more detailed errors.
            if key in Settings.LIO_YES_NO_SETTINGS:
                try:
                    value = Settings.convert_lio_yes_no(raw_value)
                except ValueError:
                    raise ValueError("expected yes or no for {}".format(key))
            else:
                try:
                    value = int(raw_value)
                except ValueError:
                    raise ValueError("expected integer for {}".format(key))
                limits = Settings.LIO_INT_SETTINGS_LIMITS.get(key)
                if limits is not None:
                    min = limits.get('min')
                    if min is not None and value < min:
                        raise ValueError("expected integer >= {} for {}".format(min, key))
                    max = limits.get('max')
                    if max is not None and value > max:
                        raise ValueError("expected integer <= {} for {}".format(max, key))
            controls[key] = value

        return controls

    @staticmethod
    def convert_lio_yes_no(value):
        """
        Convert true/false/yes/no to boolean
        """

        value = str(value).lower()
        if value in ['1', 'true', 'yes']:
            return True
        elif value in ['0', 'false', 'no']:
            return False
        raise ValueError(value)

    @staticmethod
    def normalize(k, v):
        if k == 'trusted_ip_list':
            v = v.split(',') if v else []

        if k in Settings.LIO_YES_NO_SETTINGS:
            try:
                v = Settings.convert_lio_yes_no(v)
            except Exception:
                v = True
        elif v in ['true', 'True', 'false', 'False']:
            v = strtobool(v)

        if isinstance(v, str):
            # convert any strings that hold numbers to int/float
            if Settings._float_regex.search(v):
                v = float(v)

            if Settings._int_regex.search(v):
                v = int(v)
        return v

    defaults = {"cluster_name": "ceph",
                "pool": "rbd",
                "cluster_client_name": "client.admin",
                "time_out": 30,
                "api_host": "::",
                "api_port": 5000,
                "api_secure": "true",
                "api_ssl_verify": "false",
                "loop_delay": 2,
                "trusted_ip_list": '',          # comma separate list of IPs
                "api_user": "admin",
                "api_password": "admin",
                "ceph_user": "admin",
                "debug": "false",
                "minimum_gateways": 2,
                "ceph_config_dir": '/etc/ceph',
                "priv_key": 'iscsi-gateway.key',
                "pub_key": 'iscsi-gateway-pub.key',
                "prometheus_exporter": "true",
                "prometheus_port": 9287,
                "prometheus_host": "::",
                "logger_level": logging.DEBUG
                }

    exclude_from_hash = ["cluster_client_name",
                         "logger_level"
                         ]

    target_defaults = {"osd_op_timeout": 30,
                       "dataout_timeout": 20,
                       "nopin_response_timeout": 5,
                       "nopin_timeout": 5,
                       "qfull_timeout": 5,
                       "cmdsn_depth": 128,
                       "immediate_data": "Yes",
                       "initial_r2t": "Yes",
                       "max_outstanding_r2t": 1,
                       "first_burst_length": 262144,
                       "max_burst_length": 524288,
                       "max_recv_data_segment_length": 262144,
                       "max_xmit_data_segment_length": 262144,
                       "max_data_area_mb": 8,
                       "alua_failover_type": "implicit",
                       "hw_max_sectors": "1024",

                       "block_size": 512,
                       "emulate_3pc": 1,
                       "emulate_caw": 1,
                       "emulate_dpo": 1,
                       "emulate_fua_read": 1,
                       "emulate_fua_write": 1,
                       "emulate_model_alias": 0,
                       "emulate_pr": 1,
                       "emulate_rest_reord": 1,
                       "emulate_tas": 1,
                       "emulate_tpu": 0,
                       "emulate_tpws": 0,
                       "emulate_ua_intlck_ctrl": 0,
                       "emulate_write_cache": 0,
                       "enforce_pr_isids": 1,
                       "force_pr_aptpl": 0,
                       "is_nonrot": 1,
                       "max_unmap_block_desc_count": 1,
                       "max_unmap_lba_count": 8192,
                       "max_write_same_len": 65535,
                       "optimal_sectors": 8192,
                       "pi_prot_type": 0,
                       "pi_prot_verify": 0,
                       "queue_depth": 256,
                       "unmap_granularity": 8192,
                       "unmap_granularity_alignment": 0,
                       "unmap_zeroes_data": 8192,

                       "default_cmdsn_depth": 64,
                       "default_erl": 0,
                       "login_timeout": 15,
                       "netif_timeout": 2,
                       "prod_mode_write_protect": 0,
                       "t10_pi": 0
                       }

    def __init__(self, conffile='/etc/ceph/iscsi-gateway.cfg'):

        self.error = False
        self.error_msg = ''
        self._defined_settings = []

        config = ConfigParser()
        dataset = config.read(conffile)
        if len(dataset) == 0:
            # no config file present, set up defaults
            self._define_settings(Settings.defaults)
            self._define_settings(Settings.target_defaults)
        else:
            # If we have a file use it to override the defaults
            if config.has_section("config"):
                runtime_settings = dict(Settings.defaults)
                runtime_settings.update(dict(config.items("config")))
                self._define_settings(runtime_settings)

            if config.has_section("target"):
                target_settings = dict(Settings.target_defaults)
                target_settings.update(dict(config.items("target")))
                self._define_settings(target_settings)
            else:
                # We always want these values set to at least the defaults.
                self._define_settings(Settings.target_defaults)

        self.cephconf = '{}/{}.conf'.format(self.ceph_config_dir, self.cluster_name)
        if self.api_secure:
            self.api_ssl_verify = False if self.api_secure else None

    def __repr__(self):
        s = ''
        for k in self.__dict__:
            s += "{} = {}\n".format(k, self.__dict__[k])
        return s

    def _define_settings(self, settings):
        """
        receive a settings dict and apply those key/value to the
        current instance, settings that look like numbers are converted
        :param settings: dict of settings
        :return: None
        """

        for k in settings:
            v = settings[k]
            v = self.normalize(k, settings[k])

            self._defined_settings.append(k)
            self.__setattr__(k, v)

    def hash(self):
        """
        Generates a sha256 hash of the settings that are required to be in sync between gateways.
        :return: checksum (str)
        """

        sync_settings = {}
        for setting in self._defined_settings:
            if setting not in Settings.exclude_from_hash:
                sync_settings[setting] = getattr(self, setting)

        h = hashlib.sha256()
        h.update(json.dumps(sync_settings).encode('utf-8'))
        return h.hexdigest()
