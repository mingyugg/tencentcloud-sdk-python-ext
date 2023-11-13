"""
@Description :   tencent-sdk-python-ext
@Author      :   thomas.mingyu
@Time        :   2023/11/11 22:35:48
"""

import os
import configparser

from typing import Union
from tencentcloud.common.common_client import (
    CommonClient,
    TencentCloudSDKException
)
from tencentcloud.common.credential import (
    STSAssumeRoleCredential,
    CVMRoleCredential,
    Credential
)


_CRED_PATH = os.path.join(os.path.expanduser('~'), '.tencentcloud/credentials')
_SOURCE_PROFILES = ('cvm_metadata', 'lambda')


class ProfileParser:
    def __init__(self, cred_path) -> None:
        self._parser = configparser.ConfigParser()
        self._parser.read(cred_path)

    @property
    def parser(self):
        return self._parser


class LambdaCredential:
    def __init__(self) -> None:
        self.token = os.environ.get('TENCENTCLOUD_SESSIONTOKEN')

    @property
    def secretId(self):
        return os.environ.get('TENCENTCLOUD_SECRETID')

    @property
    def secretKey(self):
        return os.environ.get('TENCENTCLOUD_SESSIONTOKEN')


class ProfileCredential:
    def __init__(self, profile: str, cred_path: str = _CRED_PATH) -> None:
        self.profile = profile
        self._cred_path = cred_path

    def get_credential(self) -> Union[Credential, STSAssumeRoleCredential]:
        """
        params:
            profile: tprofile name
            profile_path: deafult path is '~/.tencentcloud/credentials'
        des:
            support use profile to auth account and multi-account
        credentials details, such as:
            ```
                [default] (the ak/sk profile')
                secret_id:xxxx (required)
                secret_key:xxxx (required)
                token: xxxx (required)

                [profile] (the role profile)
                role_arn: xxx (required)
                session_name: xxx (default is 'tencentcloud-session')
                duration_seconds: 3600 (default is 3600)
                source_profile: xxx (required, the role'carrier)
            ```
        """
        file_path = os.path.join(
            os.path.expanduser('~'), '.tencentcloud/credentials')
        if not os.path.exists(file_path):
            raise TencentCloudSDKException('not find credentials path1')

        return self.parser_credentials()

    def parser_credentials(self) -> Union[Credential, STSAssumeRoleCredential]:

        parser = self.get_profile_parser()
        try:
            profile_obj = parser[self.profile]
        except KeyError:
            raise TencentCloudSDKException(
                f'not find profile: {self.profile}, please check the porfile')

        # if not find role_arn the profile is ak/sk'profile
        role_arn = profile_obj.get('role_arn', None)
        if role_arn is None:
            secret_id = profile_obj.get('secret_id')
            secret_key = profile_obj.get('secret_key')
            token = profile_obj.get('token')

            return Credential(secret_id, secret_key, token)

        session_name = profile_obj.get('session_name', 'tencentcloud-session')
        duration_seconds = profile_obj.get('duration_seconds', 7200)
        source_profile = profile_obj.get('source_profile')

        # if the source_profile == 'cvm_metadata', you need add the role to cvm
        # and the role must have assume the the role permmission
        if source_profile in _SOURCE_PROFILES:
            if source_profile == _SOURCE_PROFILES[0]:  # cvm_metadata
                cred = CVMRoleCredential()
            else:
                cred = LambdaCredential()

            common_client = CommonClient(
                credential=cred,
                region="ap-guangzhou",
                version='2018-08-13',
                service="sts"
            )
            params = {
                "RoleArn": role_arn,
                "RoleSessionName": session_name,
                "DurationSeconds": duration_seconds
            }
            rsp = common_client.call_json("AssumeRole", params)
            token = rsp["Response"]["Credentials"]["Token"]
            secret_id = rsp["Response"]["Credentials"]["TmpSecretId"]
            secret_key = rsp["Response"]["Credentials"]["TmpSecretKey"]

            return Credential(secret_id, secret_key, token=token)

        else:
            try:
                sp_obj = parser[source_profile]
            except KeyError:
                raise TencentCloudSDKException(f'not find source_profile: {source_profile}')

            secret_id = sp_obj.get('secret_id')
            secret_key = sp_obj.get('secret_key')
            token = sp_obj.get('token')

            return STSAssumeRoleCredential(
                secret_id, secret_key, role_arn, session_name, duration_seconds)

    def get_profile_parser(self):
        return ProfileParser(self._cred_path).parser