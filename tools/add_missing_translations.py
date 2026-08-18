# -*- coding: utf-8 -*-
"""Add missing Chinese translations for the 52 remaining untranslated entries."""
import json
import sys

sys.path.insert(0, r"F:\Game\AMS2-ZH\tools")

TRANS_PATH = r"F:\Game\AMS2-ZH\work\translations\translations.json"

# All 52 remaining Chinese translations
NEW_TRANS = {
    "Game": {
        "Game_MainMenu_QuotationLeft": "\u201c",
        "Game_MainMenu_QuotationRight": "\u201d",
        "Game_MainMenu_OpponentsHigherThanLiveries":
            "对手数量多于可用涂装数量。\n\n部分车辆将使用相同的涂装。",
        "Game_MainMenu_CustomUppercase": "自定义",
        "Game_MainMenu_PitCrewDetailLower": "维修组细节",
        "Game_MultiplayerMenus_FoundServerWaitingToJoin":
            "找到服务器：[SERVERNAME]\n但目前无法加入。\n\n等待中...",
        "Game_MultiplayerMenus_FoundServerButFull":
            "找到服务器：[SERVERNAME]\n但目前已满员。",
        "Game_MultiplayerMenus_FoundServerJoining":
            "找到服务器：[SERVERNAME]\n\n正在加入...",
        "Game_InGameMenu_WarnShootoutParcFermeWithFuel":
            "本次排位赛仅有 1 圈飞行圈；您完成本圈时的车辆设置和燃油量"
            "将作为正赛的起步设置。\n\n确定要驶出维修区吗？",
        "Game_InGameMenu_WarnShootoutParcFerme":
            "本次排位赛仅有 1 圈飞行圈；您完成本圈时的车辆设置"
            "将作为正赛的起步设置。\n\n确定要驶出维修区吗？",
        "Game_InGameMenu_WarnShootout":
            "本次排位赛仅有 1 圈飞行圈。\n\n确定要驶出维修区吗？",
        "Game_InGameMenu_WarnLapLimitParcFerme":
            "本次排位赛共有 [NUMLAPS] 圈；您完成本次排位时的车辆设置"
            "将作为正赛的起步设置。\n\n确定要驶出维修区吗？",
        "Game_InGameMenu_WarnLapLimitParcFermeWithFuel":
            "本次排位赛共有 [NUMLAPS] 圈；您完成本次排位时的车辆设置和燃油量"
            "将作为正赛的起步设置。\n\n确定要驶出维修区吗？",
        "Game_InGameMenu_WarnParcFerme":
            "本次排位结束后您的车辆设置将作为正赛的起步设置。\n\n确定要驶出维修区吗？",
        "Game_InGameMenu_WarnParcFermeWithFuel":
            "本次排位结束后您的车辆设置和燃油量将作为正赛的起步设置。\n\n确定要驶出维修区吗？",
        "Game_UI_TestDay1": "测试日",
        "Game_UI_MenuMusicVolumeLower": "菜单音乐音量",
        "Game_UI_SoundFXVolumeLower": "音效音量",
        "Game_UI_ControlSchemeLower": "控制方案",
        "Game_HelpText_OpponentFieldType":
            "您将对战的对手类别：\n\n"
            "- 相同对手：所有人使用相同车辆和涂装\n"
            "- 同级别：同级别内的不同车辆\n"
            "- 多级别：不同性能级别的多个组别",
        "Game_HelpText_OptionsCameraHeadMovement":
            "增加或座舱摄像机对赛道颠簸的平滑和过滤程度。"
            "数值越高，摄像机运动越平滑。",
        "Game_HelpText_NumberOfOpponentsType":
            "设置为\"最大可用\"时，对手数量将自动设为发车格允许的最大值。"
            "否则设置具体的 AI 对手数量。",
        "Game_HelpText_TuningSetupTractionControlSlipReversed":
            "控制牵引力控制系统的激进程度。\n\n"
            "数值越高允许更多车轮打滑（较少干预），数值越低则更早介入。",
        "Game_HelpText_LiveTrackPreset":
            "此设置允许您设定赛道表面的起始状态，"
            "包括赛道温度、湿度和橡胶附着层。",
        "Game_HelpText_OptionsGameTuningEditUsesRanges":
            "设置为\"单位\"时，车辆设置界面中的悬挂设置将以范围滑块显示。"
            "设置为\"格数\"时，将以离散格数值显示。",
        "Game_HelpText_ICMResetStrategy":
            "决定车内管理菜单重新打开时是保持当前菜单位置还是重置到根菜单。",
        "Game_HelpText_TuningSetupSteeringLock":
            "转向锁角是前轮的最大旋转度数。"
            "宽弯道的高速赛道应减小此值，紧凑技术性赛道应增大此值。",
        "Game_HelpText_ControlsAssignment":
            "控制分配：\n\n"
            "点击或激活要编辑的分配行，然后按下期望的按钮或移动轴以完成分配。",
        "Game_HelpText_TrackMapMode":
            "设置 HUD 赛道地图的模式。\n\n"
            "\"静态\"模式显示固定的完整赛道地图。"
            "\"动态\"模式会旋转和缩放以聚焦玩家当前位置。",
        "Game_HelpText_FFBType":
            "- 自定义：仅提供转向轴方向的转向力矩，无路面振动、阻尼和路肩效果。\n"
            "- 沉浸：提供更沉浸的体验，包含路面效果和路肩振动。",
        "Game_HelpText_OptionGameRandomFailures":
            "随机故障决定您的车辆（包括 AI）在比赛中是否会发生随机机械故障。",
        "Game_HelpText_RulesRegulationsLimitedSetup":
            "封闭区规则：车辆在排位赛中首次驶出维修区后，"
            "其设置在正赛开始前无法更改。",
        "Game_HelpText_ParallaxOcclusionQuality":
            "视差遮蔽贴图为平坦物体增加深度和光照效果，而不增加几何复杂度。"
            "更高的设置以性能为代价提升视觉质量。",
    },
    "Platform": {
        "Platform_ControllerPresets_FanatecDD1Combine": "Fanatec DD1 Formula V2 方向盘\n踏板合并",
        "Platform_ControllerPresets_FanatecDD1PS4Combine": "Fanatec DD1 PS4 Formula V2 方向盘\n踏板合并",
        "Platform_ControllerPresets_FanatecDD1Seperate": "Fanatec DD1 Formula V2 方向盘\n踏板分离",
        "Platform_ControllerPresets_FanatecDD1PS4Seperate": "Fanatec DD1 PS4 Formula V2 方向盘\n踏板分离",
        "Platform_ControllerPresets_FanatecDD2Combine": "Fanatec DD2 Formula V2 方向盘\n踏板合并",
        "Platform_ControllerPresets_FanatecDD2Seperate": "Fanatec DD2 Formula V2 方向盘\n踏板分离",
        "Platform_ControllerPresets_DDGenericCombined": "直驱通用方向盘\n踏板合并",
        "Platform_ControllerPresets_DDGenericSeparate": "直驱通用方向盘\n踏板分离",
        "Platform_SaveGame_ProfileOverNo": "否",
        "Platform_SaveGame_ProfileOverText": "确定要覆盖此档案吗？",
        "Platform_SaveGame_ProfileOverTitle": "覆盖档案",
        "Platform_SaveGame_ProfileOverYes": "是",
        "Platform_System_Xbox360SigninChangeTitle": "更改登录",
        "Platform_System_Xbox360InviteFromInactiveControllerTitle": "来自非活动控制器的邀请",
        "Platform_System_Xbox360DLCDeviceEjectTitle": "设备已移除",
    },
    "RAC": {
        "RAC_HUD_ThousandSeparator": ",",
        "RAC_HUD_RaceComplete": "比赛完成",
        "RAC_HUD_SectorSplitTimesMessages": "分段计时",
        "RAC_UI_SteeringLeft": "左转",
    },
}


def main():
    with open(TRANS_PATH, encoding="utf-8") as f:
        trans = json.load(f)

    added = 0
    fixed = 0
    for table, entries in NEW_TRANS.items():
        if table not in trans:
            trans[table] = {}
        for key, zh_val in entries.items():
            old = trans[table].get(key)
            if old is None:
                trans[table][key] = zh_val
                added += 1
            elif old.startswith("UNTRANSLATED"):
                trans[table][key] = zh_val
                fixed += 1

    with open(TRANS_PATH, "w", encoding="utf-8") as f:
        json.dump(trans, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in trans.values())
    print("新增: %d 条翻译" % added)
    print("修复: %d 条 UNTRANSLATED 占位符" % fixed)
    print("总计: %d 条翻译，覆盖 %d 个表" % (total, len(trans)))


if __name__ == "__main__":
    main()
