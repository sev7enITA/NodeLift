# NodeLift — 简体中文

**让已有硬件在本地 AI 中继续发挥作用。**

NodeLift 是由 **Fabrizio Degni** 发起和开发的实验性项目。手机上的小型草稿模型可以提出候选词元，电脑上的主模型随后进行验证。目前不会将手机内存合并到目标模型的可用内存中，也尚未证明实体手机能加速单次推理。

应用默认使用英语。通过 **Language** 选择 **简体中文** 或 **Italiano**，选择会保存在本地，翻译无需联网。当前配套应用版本为 **0.2.3 / build 5**；主机源码包含 0.3.0 集成预览。

- [实验性下载](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.3)：Android 实验室 APK；iOS 为未签名构建，安装前需要 Apple 签名和配置。
- 先完成[电脑端入门](../wiki/Quickstart.md)，再连接 [Android](../wiki/Android.md) 或 [iPhone/iPad](../wiki/iOS-and-iPadOS.md)。详细技术指南目前以英语为主。
- [模型与提供商](../wiki/Models-and-providers.md)、[本地化和验证](../LOCALIZATION.md)、[基准测试](../wiki/Benchmarking.md)。
- [Wiki](https://github.com/sev7enITA/NodeLift/wiki)、[图片](../GALLERY.md)、[项目展示](https://www.fabriziodegni.com/NodeLift/)。

Hugging Face 下载和直接导入支持完整的单文件 GGUF。OpenRouter 是可选的云端路径，会发送提示词且可能产生费用。LM Studio/oMLX 本地 API 路径与手机草稿推理分开，不会自动获得手机加速。

在最初的小型控制模型测试中，本地草稿比仅运行目标模型更慢。项目保留并公开负面结果。编译成功或 CI 通过并不等于实体设备性能已经得到验证。

[English](../../README.md) · [Italiano](README_it.md) · [参与贡献](../../CONTRIBUTING.md)
