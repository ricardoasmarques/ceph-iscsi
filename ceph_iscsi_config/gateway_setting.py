import logging


def convert_str_to_bool(value):
    """
    Convert true/false/yes/no/1/0 to boolean
    """

    if isinstance(value, bool):
        return value

    value = str(value).lower()
    if value in ['1', 'true', 'yes']:
        return True
    elif value in ['0', 'false', 'no']:
        return False
    raise ValueError(value)


class Setting(object):
    def __init__(self, name, type_str, def_val):
        self.name = name
        self.type_str = type_str
        self.def_val = def_val

    def __contains__(self, key):
        return key == self.def_val


class BoolSetting(Setting):
    def __init__(self, name, def_val):
        super(BoolSetting, self).__init__(name, "bool", def_val)

    def to_str(self, norm_val):
        if norm_val:
            return "true"
        else:
            return "false"

    def normalize(self, raw_val):
        try:
            # for compat we also support Yes/No and 1/0
            return convert_str_to_bool(raw_val)
        except ValueError:
            raise ValueError("expected true or false for {}".format(self.name))


class LIOBoolSetting(BoolSetting):
    def __init__(self, name, def_val):
        super(LIOBoolSetting, self).__init__(name, def_val)

    def to_str(self, norm_val):
        if norm_val:
            return "yes"
        else:
            return "no"

    def normalize(self, raw_val):
        try:
            # for compat we also support True/False and 1/0
            return convert_str_to_bool(raw_val)
        except ValueError:
            raise ValueError("expected yes or no for {}".format(self.name))


class ListSetting(Setting):
    def __init__(self, name, def_val):
        super(ListSetting, self).__init__(name, "list", def_val)

    def to_str(self, norm_val):
        return str(norm_val)

    def normalize(self, raw_val):
        return raw_val.split(',') if raw_val else []


class StrSetting(Setting):
    def __init__(self, name, def_val):
        super(StrSetting, self).__init__(name, "str", def_val)

    def to_str(self, norm_val):
        return str(norm_val)

    def normalize(self, raw_val):
        return str(raw_val)


class IntSetting(Setting):
    def __init__(self, name, min_val, max_val, def_val):
        self.min_val = min_val
        self.max_val = max_val
        super(IntSetting, self).__init__(name, "int", def_val)

    def to_str(self, norm_val):
        return str(norm_val)

    def normalize(self, raw_val):
        try:
            val = int(raw_val)
        except ValueError:
            raise ValueError("expected integer for {}".format(self.name))

        if val < self.min_val:
            raise ValueError("expected integer >= {} for {}".
                             format(self.min_val, self.name))
        if val > self.max_val:
            raise ValueError("expected integer <= {} for {}".
                             format(self.max_val, self.name))
        return val


class EnumSetting(Setting):
    def __init__(self, name, def_val, valid_vals):
        self.valid_vals = valid_vals
        super(EnumSetting, self).__init__(name, "enum", def_val)

    def to_str(self, norm_val):
        return str(norm_val)

    def normalize(self, raw_val):
        norm_val = str(raw_val)

        if norm_val not in self.valid_vals:
            raise ValueError("expected {}".format(self.valid_vals))

        return norm_val


CLIENT_SETTINGS = {
    "dataout_timeout": IntSetting("dataout_timeout", 2, 60, 20),
    "nopin_response_timeout": IntSetting("nopin_response_timeout", 3, 60, 5),
    "nopin_timeout": IntSetting("nopin_timeout", 3, 60, 5),
    "cmdsn_depth": IntSetting("cmdsn_depth", 1, 512, 128)}

TGT_SETTINGS = {
    # client settings you can also set at the ceph-iscsi target level
    "dataout_timeout": IntSetting("dataout_timeout", 2, 60, 20),
    "nopin_response_timeout": IntSetting("nopin_response_timeout", 3, 60, 5),
    "nopin_timeout": IntSetting("nopin_timeout", 3, 60, 5),
    "cmdsn_depth": IntSetting("cmdsn_depth", 1, 512, 128),
    # lio tpg settings
    "immediate_data": LIOBoolSetting("immediate_data", True),
    "initial_r2t": LIOBoolSetting("initial_r2t", True),
    "max_outstanding_r2t": IntSetting("max_outstanding_r2t", 1, 65535, 1),
    "first_burst_length": IntSetting("first_burst_length", 512, 16777215, 262144),
    "max_burst_length": IntSetting("max_burst_length", 512, 16777215, 524288),
    "max_recv_data_segment_length": IntSetting("max_recv_data_segment_length",
                                               512, 16777215, 262144),
    "max_xmit_data_segment_length": IntSetting("max_xmit_data_segment_length",
                                               512, 16777215, 262144)}

SYS_SETTINGS = {
    "cluster_name": StrSetting("cluster_name", "ceph"),
    "pool": StrSetting("pool", "rbd"),
    "cluster_client_name": StrSetting("cluster_client_name", "client.admin"),
    "time_out": IntSetting("time_out", 1, 600, 30),
    "api_host": StrSetting("api_host", "::"),
    "api_port": IntSetting("api_port", 1, 65535, 5000),
    "api_secure": BoolSetting("api_secure", True),
    "api_ssl_verify": BoolSetting("api_ssl_verify", False),
    "loop_delay": IntSetting("loop_delay", 1, 60, 2),
    "trusted_ip_list": ListSetting("trusted_ip_list", []),  # comma separate list of IPs
    "api_user": StrSetting("api_user", "admin"),
    "api_password": StrSetting("api_password", "admin"),
    "ceph_user": StrSetting("ceph_user", "admin"),
    "debug": BoolSetting("debug", False),
    "minimum_gateways": IntSetting("minimum_gateways", 2, 9999, 2),
    "ceph_config_dir": StrSetting("ceph_config_dir", '/etc/ceph'),
    "priv_key": StrSetting("priv_key", 'iscsi-gateway.key'),
    "pub_key": StrSetting("pub_key", 'iscsi-gateway-pub.key'),
    "prometheus_exporter": BoolSetting("prometheus_exporter", True),
    "prometheus_port": IntSetting("prometheus_port", 1, 65535, 9287),
    "prometheus_host": StrSetting("prometheus_host", "::"),
    "logger_level": IntSetting("logger_level", logging.DEBUG, logging.CRITICAL,
                               logging.DEBUG),
    # TODO: This is under sys for compat. It is not settable per device/backend
    # type yet.
    "alua_failover_type": EnumSetting("alua_failover_type", "implicit",
                                      ["implicit"])}

# TODO rimarques Check all usages of this
TCMU_SETTINGS = {
    "max_data_area_mb": IntSetting("max_data_area_mb", 1, 2048, 8),
    "qfull_timeout": IntSetting("qfull_timeout", 0, 600, 5),
    "osd_op_timeout": IntSetting("osd_op_timeout", 0, 600, 30),
    "hw_max_sectors": IntSetting("hw_max_sectors", 1, 8192, 1024)}

KERNEL_SETTINGS = {
    "block_size": IntSetting("max_data_area_mb", 512),
}

# "block_size": 512,
# "emulate_3pc": 1,
# "emulate_caw": 1,
# "emulate_dpo": 1,
# "emulate_fua_read": 1,
# "emulate_fua_write": 1,
# "emulate_model_alias": 0,
# "emulate_pr": 1,
# "emulate_rest_reord": 1,
# "emulate_tas": 1,
# "emulate_tpu": 0,
# "emulate_tpws": 0,
# "emulate_ua_intlck_ctrl": 0,
# "emulate_write_cache": 0,
# "enforce_pr_isids": 1,
# "force_pr_aptpl": 0,
# "is_nonrot": 1,
# "max_unmap_block_desc_count": 1,
# "max_unmap_lba_count": 8192,
# "max_write_same_len": 65535,
# "optimal_sectors": 8192,
# "pi_prot_type": 0,
# "pi_prot_verify": 0,
# "queue_depth": 256,
# "unmap_granularity": 8192,
# "unmap_granularity_alignment": 0,
# "unmap_zeroes_data": 8192,
#
# "default_cmdsn_depth": 64,
# "default_erl": 0,
# "login_timeout": 15,
# "netif_timeout": 2,
# "prod_mode_write_protect": 0,
# "t10_pi": 0
