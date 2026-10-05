<div align="center">

# GKI KernelSU SUSFS

**Automated GKI Kernel Builds | SukiSU / ReSukiSU + SUSFS Integration**

[![Release](https://img.shields.io/github/v/release/LingLuo17/AnyKernel3?label=Release&style=flat-square&logo=github&logoColor=white&color=2ea44f)](https://github.com/LingLuo17/AnyKernel3/releases)
[![Coolapk](https://img.shields.io/badge/Follow-Coolapk-3DDC84?style=flat-square&logo=android&logoColor=white)](http://www.coolapk.com/u/38407386)
[<img src="https://img.shields.io/badge/Join-QQ%20Group-blue?style=flat-square&logo=github&logoColor=white">](https://qm.qq.com/q/PZIFvlcbqU)
[![SukiSU](https://img.shields.io/badge/SukiSU-Supported-5AA300?style=flat-square)](https://sukisu.org/)
[![ReSukiSU](https://img.shields.io/badge/ReSukiSU-Supported-5AA300?style=flat-square)](https://resukisu.github.io/)
[![SUSFS](https://img.shields.io/badge/SUSFS-Integrated-E67E22?style=flat-square)](https://gitlab.com/simonpunk/susfs4ksu)

**English** | [简体中文](#chinese)

</div>

## 📖 Introduction

Built upon [AnyKernel3](https://github.com/osm0sis/AnyKernel3), this repository uses GitHub Actions to automatically compile Android GKI kernels. It integrates multiple KernelSU variants and SUSFS kernel-level spoofing solutions Add practical patches such as ZRAM and BBG.

- The build workflows are adapted from [zzh20188/GKI_KernelSU_SUSFS](https://github.com/zzh20188/GKI_KernelSU_SUSFS) and [Wild Kernels](https://github.com/WildKernels/GKI_KernelSU_SUSFS)
- Flashing rule: ***It can be flashed as long as the kernel version matches.*** The package performs **no boot/kernel version check**; the target Android system range is selected at build time via the `a17_compat` switch (**Android 12-16 by default; Android 17 only when enabled**). The `androidXX` in a build name is the GKI branch the kernel was built from (its KMI), **not** the required system version.

## 📦 Supported Kernel Versions

| Android | Kernel Version | Manual Workflow |
|:---:|:---:|:---:|
| 12 | 5.10 | `kernel-a12-5-10.yml` |
| 13 | 5.15 | `kernel-a13-5-15.yml` |
| 14 | 6.1 | `kernel-a14-6-1.yml` |
| 15 | 6.6 | `kernel-a15-6-6.yml` |
| 16 | 6.12 | `kernel-a16-6-12.yml` |
| Custom | Any | `kernel-custom.yml` |

> 📱 **System version compatibility**: kernel version and Android system version are independent under GKI. As long as the device's current GKI kernel version matches the zip (5.10 ↔ 5.10, 6.6 ↔ 6.6, …), the package flashes and boots on its target systems — chosen at build time: **Android 12-16 by default, or Android 17 with the `a17_compat` switch**. Devices that keep the generic ramdisk in `init_boot` (Android 13+) are detected automatically and flashed kernel-only.

## ✨ Features

| Feature | Description |
|:---|:---|
| 🔐 KernelSU Variants | Supports SukiSU / ReSukiSU variants, selectable at build time |
| 🙈 SUSFS | Kernel-level hiding working with KSU to complete environment spoofing |
| 💾 ZRAM LZ4 | ZRAM Compression Algorithm Patch |
| 🛡️ BBG (Baseband Guard) | BBG patch to protect the baseband partitions from accidental wipe |
| 🌐 Network enhancement | Optional IPSet + BBR kernel config (BBR default congestion control, fq/fq_codel qdisc, full IPSet types up to 65534 sets, IPv6 NAT/masquerade, extra congestion algorithms) |
| ⚡ KPM | Optional KPM feature / build-time patching |
| 🔔 Re-Kernel | Optional Re-Kernel driver integration |
| 🩹 CVE-2026-43499 | Optional automatic application of the rtmutex fix |
| 🐳 Droidspaces | Optional container support with NTSync kernel compatibility patch |
| 🧩 Skip Incompatible | Optional: auto-skip incompatible or unusable features (except SUSFS) instead of failing the build |
| ✅ 支持Android17 | 开启即支持 Android 17 系统版本，但仅 Android 17 系统版本可刷入；关闭即不支持 Android 17 系统版本，Android 12-16 均可刷入 |

## 🚀 Usage

1. **Fork this repository** (or use it directly)
2. Go to the **Actions** page and pick the workflow for your kernel version
3. Click **Run workflow** and fill in the parameters as needed:
   - `android_version` / `kernel_version` / `sub_level` / `os_patch_level`
   - `ksu_variant`: KernelSU variant (SukiSU / ReSukiSU)
   - Feature switches: `enable_susfs`, `use_zram`, `use_bbg`, `use_net_enhance`, `use_kpm`, `skip_incompatible`, etc.
4. Once the build finishes, download the **Artifacts** from the run page:
   - `AnyKernel3.zip` — flashable zip (recommended; flash via custom Recovery or KSU)
   - `boot.img` / `boot-gz.img` / `boot-lz4.img` — boot images for each compression format

> 💡 Artifacts are uploaded as Actions Artifacts by default and are not auto-published as Releases. Failed runs additionally upload build logs (`Build-Logs`) and patch conflict records (`Rejects`) for troubleshooting.

## 🔧 Custom Commit Configuration

The [`config/config`](config/config) file lets you pin specific commits for SUSFS and SukiSU.

**What is a commit?**

A commit is a hash string representing the state of a repository at a certain point in time. For example, setting SukiSU to `4b8644515fe6d87a109129e590ccd9d33a855dca` means the kernel will be built with the SukiSU version from January 30.

**Why pin a commit?**

- Roll back to a stable version when upstream updates introduce bugs or compatibility issues
- Manually specify a compatible version when SUSFS and SukiSU are out of sync and the build fails

**How to get a commit hash?**

- SUSFS: [susfs4ksu](https://gitlab.com/simonpunk/susfs4ksu) (GitLab → Repository → Commits)
- SukiSU: [SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra/commits) (GitHub commit history page)

## 🛠️ Recommended After Installation
### 🔧 Xposed Modules
| Module | Description |
|:---:|:---|
| **FuseFixer** | [Unicode zero-width character fix module](https://github.com/5ec1cff/FuseFixer) |

## 🙏 Acknowledgments

- [osm0sis/AnyKernel3](https://github.com/osm0sis/AnyKernel3)
- [zzh20188/GKI_KernelSU_SUSFS](https://github.com/zzh20188/GKI_KernelSU_SUSFS) / [WildKernels/GKI_KernelSU_SUSFS](https://github.com/WildKernels/GKI_KernelSU_SUSFS) / [LingLuo17/AnyKernel3](https://github.com/LingLuo17/AnyKernel3)
- [SukiSU](https://sukisu.org/) / [ReSukiSU](https://resukisu.github.io/)
- [SUSFS](https://gitlab.com/simonpunk/susfs4ksu)
- [YuzakiKokuban/android_kernel_xiaomi_sm8850](https://github.com/YuzakiKokuban/android_kernel_xiaomi_sm8850)
- [cctv18/android_gki_kernel_common](https://github.com/cctv18/android_gki_kernel_common) — `android16-6.12-2025-06`

<div align="center">

## ⚠️ Disclaimer

</div>

- Flashing this kernel will not void your warranty, but there is always a risk of bricking your device. Please make sure to:
- 💾 Back up your data
- 🧠 Understand the risks before proceeding

- Please make sure to back up the original boot image of this system in advance.

- If flashing AnyKernel3 causes your device to enter an infinite boot loop or fail to boot, enter BootLoader and flash the original boot image back.

- I take no responsibility for any issues caused by flashing this kernel.

<div align="center">
  
# **🚨 Proceed at your own risk!**

</div>
