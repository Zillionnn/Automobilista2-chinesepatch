# -*- coding: utf-8 -*-
"""Fix translation quality: correct errors and translate visible Chinese=English entries.

Only overrides entries that are clearly wrong or should be in Chinese.
Skips: brand names, format strings, unit symbols, social media names.
"""
import json

TRANS_PATH = r"F:\Game\AMS2-ZH\work\translations\translations.json"

QUALITY_FIXES = {
    "Game": {
        # === 修复明显错误 ===
        "Game_MainMenu_instantAction": "即时行动",
        "Game_MainMenu_audio": "音频",
        "Game_MainMenu_Audio2": "音频",
        "Game_MainMenu_Audio3": "音频",
        "Game_MainMenu_credits": "制作人员",

        # === 菜单标签 ===
        "Game_MainMenu_AvoidUser": "屏蔽用户",
        "Game_MainMenu_Free": "免费",
        "Game_MainMenu_Year2": "年份：",
        "Game_MainMenu_Slow": "最小",
        "Game_MainMenu_Fast": "最大",
        "Game_MainMenu_Under": "低于",
        "Game_MainMenu_Over": "超过",
        "Game_MainMenu_Enter": "确认",
        "Game_MainMenu_Esports": "电子竞技",
        "Game_MainMenu_OnlineFreePractice": "在线自由练习",
        "Game_MainMenu_OnlineFreePractice1": "在线自由练习",
        "Game_MainMenu_StandingsPowerRankin": "积分榜与实力排名",
        "Game_MainMenu_StandingsResults": "积分榜与成绩",
        "Game_MainMenu_Founded": "成立于",
        "Game_MainMenu_HomeTrack": "主场赛道",
        "Game_MainMenu_PageSpecificHelpText": "页面专属帮助文本",
        "Game_MainMenu_TestTrack": "测试赛道",
        "Game_MainMenu_Foc": "焦点锐化深度",
        "Game_MainMenu_Foc2": "焦点衰减深度",
        "Game_MainMenu_Bhp": "(马力)",

        # === 帮助文本和提示 ===
        "Game_MainMenu_AZ": "A-Z",
    },
    "Pit": {
        # === 维修工程师语音 ===
        "Pit_Engineer_PitReleaseA1a": "走，走！",
        "Pit_Engineer_PitReleaseA1b": "走，走！",
        "Pit_Engineer_PitReleaseA1c": "走，走！",
        "Pit_Engineer_PitReleaseA1d": "走，走！",
        "Pit_Engineer_PitReleaseA1e": "走，走！",
        "Pit_Engineer_PitReleaseA4a": "走，走，走！",
        "Pit_Engineer_PitReleaseA4b": "走，走，走！",
        "Pit_Engineer_PitReleaseA4c": "走，走，走！",
        "Pit_Engineer_PitReleaseA4d": "走，走，走！",
        "Pit_Engineer_PitReleaseA4e": "走，走，走！",
        "Pit_Engineer_PitReleaseA4f": "走，走，走！",
        "Pit_Engineer_PitReleaseA4g": "走，走，走！",
        "Pit_Engineer_PitReleaseA4h": "走，走，走！",
    },
    "RAC": {
        # === HUD 消息 ===
        "RAC_HUD_HotLapGoal": "击败目标时间",
        "RAC_HUD_HotLap1star": "你击败了一个目标，继续挑战下一个！",
        "RAC_HUD_HotLap2stars": "你击败了两个目标，只差最后一个！",
        "RAC_HUD_HotLap3stars": "你击败了所有目标，干得漂亮！",
        "RAC_HUD_HotLapTooSlow": "你未达到最低圈速",
        "RAC_HUD_STAROBJECTIVES": "星级目标",
        "RAC_HUD_PenaltySmokeViolationText": "轮胎烟雾违规",
        "RAC_HUD_PenaltyClimbingInTheGateText": "爬墙违规",
        "RAC_HUD_WarningFormLapCollision": "暖胎圈碰撞警告",

        # === 控制项 ===
        "RAC_Controls_ActiveSuspensionReactionSpeed": "主动悬挂反应速度",
        "RAC_Controls_ActiveSuspensionDamping": "主动悬挂阻尼",
    },
    "Platform": {
        "Platform_ControllerPresets_PCCustomWheelLoFi": "传统方向盘",
    },
}


def main():
    with open(TRANS_PATH, encoding="utf-8") as f:
        trans = json.load(f)

    added = 0
    updated = 0
    for table, entries in QUALITY_FIXES.items():
        if table not in trans:
            trans[table] = {}
        for key, zh_val in entries.items():
            old = trans[table].get(key)
            if old is None:
                trans[table][key] = zh_val
                added += 1
            elif old != zh_val:
                trans[table][key] = zh_val
                updated += 1

    with open(TRANS_PATH, "w", encoding="utf-8") as f:
        json.dump(trans, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in trans.values())
    print("新增: %d 条" % added)
    print("更新: %d 条（修复翻译错误和质量改进）" % updated)
    print("总计: %d 条翻译，覆盖 %d 个表" % (total, len(trans)))


if __name__ == "__main__":
    main()
