# NodeLift — 简体中文

**让已有硬件在本地 AI 中继续发挥作用。**

[![MIT 许可证](https://img.shields.io/badge/License-MIT-lightgrey.svg)](../../LICENSE)
[![项目展示](https://img.shields.io/badge/Showcase-Live-146c6a.svg)](https://www.fabriziodegni.com/NodeLift/)
[![配套应用 0.2.3 预发布版](https://img.shields.io/badge/Companion-0.2.3%20prerelease-b45309.svg)](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.3)
[![主机 0.3.0 预览版](https://img.shields.io/badge/Host-0.3.0%20preview-b45309.svg)](../../docs/INTEGRATIONS.md)

[![源码检查](https://github.com/sev7enITA/NodeLift/actions/workflows/checks.yml/badge.svg?branch=main)](https://github.com/sev7enITA/NodeLift/actions/workflows/checks.yml)
[![文档检查](https://github.com/sev7enITA/NodeLift/actions/workflows/documentation.yml/badge.svg?branch=main)](https://github.com/sev7enITA/NodeLift/actions/workflows/documentation.yml)
[![原生构建检查](https://github.com/sev7enITA/NodeLift/actions/workflows/native-build.yml/badge.svg?branch=main)](https://github.com/sev7enITA/NodeLift/actions/workflows/native-build.yml)
[![发布文件验证](https://github.com/sev7enITA/NodeLift/actions/workflows/release-verification.yml/badge.svg?branch=main)](https://github.com/sev7enITA/NodeLift/actions/workflows/release-verification.yml)

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776ab.svg)](../../docs/wiki/Quickstart.md)
[![C++17](https://img.shields.io/badge/C%2B%2B-17-00599c.svg)](../../native/CMakeLists.txt)
[![固定版本的 llama.cpp](https://img.shields.io/badge/llama.cpp-pinned-146c6a.svg)](../../native/llama.lock)
[![界面：英语、简体中文、意大利语](https://img.shields.io/badge/UI-EN%20%7C%20zh--Hans%20%7C%20IT-146c6a.svg)](../../docs/LOCALIZATION.md)

源码和文档徽章跟踪 `main`；原生构建和发布文件验证徽章显示最近一次手动运行。

NodeLift 是由 **Fabrizio Degni** 发起和开发的实验性项目。手机上的小型草稿模型可以提出候选词元，电脑上的主模型随后进行验证。目前不会将手机内存合并到目标模型的可用内存中，也尚未证明实体手机能加速单次推理。

应用默认使用英语。通过 **Language** 选择 **简体中文** 或 **Italiano**，选择会保存在本地，翻译无需联网。当前配套应用版本为 **0.2.3 / build 5**；主机源码包含 0.3.0 集成预览。

- [实验性下载](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.3)：Android 实验室 APK；iOS 为未签名构建，安装前需要 Apple 签名和配置。
- 先完成[电脑端入门](../wiki/Quickstart.md)，再连接 [Android](../wiki/Android.md) 或 [iPhone/iPad](../wiki/iOS-and-iPadOS.md)。详细技术指南目前以英语为主。
- [模型与提供商](../wiki/Models-and-providers.md)、[本地化和验证](../LOCALIZATION.md)、[基准测试](../wiki/Benchmarking.md)。
- [Wiki](https://github.com/sev7enITA/NodeLift/wiki)、[图片](../GALLERY.md)、[项目展示](https://www.fabriziodegni.com/NodeLift/)。
- [设备关系图与贡献说明](../DEVICE-GRAPH.md)：硬件、历史遥测和已接受的移动端提案占比；该占比不代表计算利用率或加速比。

Hugging Face 下载和直接导入支持完整的单文件 GGUF。OpenRouter 是可选的云端路径，会发送提示词且可能产生费用。LM Studio/oMLX 本地 API 路径与手机草稿推理分开，不会自动获得手机加速。

在最初的小型控制模型测试中，本地草稿比仅运行目标模型更慢。项目保留并公开负面结果。编译成功或 CI 通过并不等于实体设备性能已经得到验证。

[English](../../README.md) · [Italiano](README_it.md) · [参与贡献](../../CONTRIBUTING.md)
