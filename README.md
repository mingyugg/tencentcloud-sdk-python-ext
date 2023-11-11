# tencent-sdk-python-ext
腾讯云Python Sdk 插件，包含以下功能的的扩展

- [凭证管理](#凭证管理)

安装方式
```
pip install tencent-sdk-python-ext
```

## 凭证管理

### 通过本地文件配置Profile的方式配置多种认证方式
- 配置多个ak/sk
- 通过role的方式，配置多个role，role的载体包含以下几种方式
  - ak/sk，载体为ak/sk
  - cvm_metadata，载体为虚机角色
  - lambda，载体为云函数的角色

本地配置的默认路径为~/.tencentcloud/credentials, 详情请[查看配置文件demo](./demo/credentials)（重要）

```
from tcc_ext.credentials import ProfileCredential

credential = ProfileCredential("test")

```
### 云函数角色权限认证
```
from tcc_ext.credentials import LambdaCredential

credential = LambdaCredential()
```

