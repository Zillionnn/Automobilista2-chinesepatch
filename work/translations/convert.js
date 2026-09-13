// all_entries.json -> translations.json 台式术语转大陆规范 + 人工修正
// 用法: node convert.js [--dry]
const fs = require('fs');
const path = require('path');
const DIR = __dirname;
const DRY = process.argv.includes('--dry');

const all = JSON.parse(fs.readFileSync(path.join(DIR, 'all_entries.json'), 'utf8'));
const existing = JSON.parse(fs.readFileSync(path.join(DIR, 'translations.json'), 'utf8'));

// ---------- 1. 术语词典（顺序敏感：长词/复合词在前） ----------
const termDict = [
  // 引号
  ['「', '\u201C'], ['」', '\u201D'], ['『', '\u2018'], ['』', '\u2019'],
  // 复合优先
  ['网际网路', '互联网'],
  ['力回馈', '力反馈'],
  ['回馈', '反馈'],
  ['防死锁煞车', '防抱死刹车'],
  ['防锁死煞车', '防抱死刹车'],
  ['煞车分配器', '刹车平衡'],
  ['煞车', '刹车'],
  ['滑鼠', '鼠标'],
  ['萤幕', '屏幕'],
  ['讯息', '信息'],
  ['资讯', '信息'],
  ['网路', '网络'],
  ['登入', '登录'],
  ['登陆', '登录'],
  ['登出', '注销'],
  ['储存装置', '存储设备'],
  ['储存', '保存'],
  ['视窗', '窗口'],
  ['载入', '加载'],
  ['硬体', '硬件'],
  ['软体', '软件'],
  ['支援', '支持'],
  ['影格', '帧'],
  ['使用者名称', '用户名'],
  ['使用者端', '客户端'],
  ['使用者', '用户'],
  // 预设：仅修正真正的 default 语境，preset 语境保留"预设"
  ['预设日期', '默认日期'],
  ['预设设定', '默认调校'],
  ['预设状态', '默认状态'],
  ['还原为预设', '恢复默认'],
  ['预设中，', '默认情况下，'],
  ['旗子', '旗帜'],
  ['水准', '水平'],
  ['详阅', '仔细阅读'],
  ['导引', '引导'],
  ['空力套件', '空气动力学套件'],
  ['空力', '空气动力学'],
  ['停站', '进站'],
  ['行车线', '走线'],
  ['排档杆', '换挡杆'],
  ['排档', '挡'],
  ['档位', '挡位'],
  ['换档', '换挡'],
  ['升档', '升挡'],
  ['降档', '降挡'],
  ['进档', '升挡'],
  ['退档', '降挡'],
  ['自订', '自定义'],
  ['线上', '在线'],
  ['建立', '创建'],
  ['收件匣', '收件箱'],
  ['契约', '合同'],
  ['邀约', '邀请'],
  ['名誉', '信誉'],
  ['展示房', '展厅'],
  ['焦长', '焦距'],
  ['进阶', '高级'],
  ['立刻', '立即'],
  ['不只', '不仅'],
  ['阶级', '等级'],
  ['测时赛', '计时赛'],
  ['实况', '直播'],
  ['社群', '社区'],
  ['视点', '视角'],
  ['摄影机', '摄像机'],
  ['扭力', '扭矩'],
  ['藉由', '通过'],
  ['维修中', '维护中'],
  ['搜寻', '搜索'],
  ['停权', '封禁'],
  ['帐户', '账户'],
  ['操作杆', '摇杆'],
  ['飘移', '漂移'],
  ['倒数计时', '倒计时'],
  ['区段', '分段'],
  ['冷胎圈', '冷却圈'],
  ['控制器避震', '控制器阻尼'],
  ['共享纪录', '共享内存'],
  ['内线', '内侧'],
  ['外线', '外侧'],
  ['螺帽', '螺母'],
  ['妳', '你'],
  // 换挡与设置用语
  ['重设教学', '重置教程'],
  ['重设', '重置'],
  ['重置为预设', '重置为默认'],
  ['教学', '教程'],
  ['赛车周末', '比赛周末'],
  ['升降排文件', '升降挡'],
  ['车辆设定', '车辆调校'],
  ['设定', '设置'],
];

// ---------- 2. 正则规则（在字符串词典之后） ----------
const regexRules = [
  [/自定(?!义)/g, '自定义'],
  [/(?<!存)档(?!案)/g, '挡'],
  [/么？/g, '吗？'],
  [/么\?/g, '吗?'],
];

// ---------- 3. 国家名全值映射（台式 -> 大陆规范） ----------
const countryMap = {
  '义大利': '意大利', '纽西兰': '新西兰', '斯洛维尼亚': '斯洛文尼亚', '克罗埃西亚': '克罗地亚',
  '哥斯大黎加': '哥斯达黎加', '沙乌地阿拉伯': '沙特阿拉伯', '多明尼加': '多米尼加',
  '列支敦斯登': '列支敦士登', '马尔他': '马耳他', '巴布亚纽几内亚': '巴布亚新几内亚',
  '阿拉伯联合大公国': '阿拉伯联合酋长国', '千里达及托巴哥': '特立尼达和多巴哥',
  '塞浦勒斯': '塞浦路斯', '安地瓜': '安提瓜和巴布达', '亚塞拜然': '阿塞拜疆',
  '贝里斯': '伯利兹', '贝南': '贝宁', '波札那': '博茨瓦纳', '汶莱': '文莱',
  '布吉纳法索': '布基纳法索', '蒲隆地': '布隆迪', '维德角': '佛得角', '查德': '乍得',
  '葛摩': '科摩罗', '吉布地': '吉布提', '厄瓜多': '厄瓜多尔', '厄利垂亚': '厄立特里亚',
  '衣索比亚': '埃塞俄比亚', '加彭': '加蓬', '甘比亚': '冈比亚', '乔治亚': '格鲁吉亚',
  '格瑞纳达': '格林纳达', '瓜地马拉': '危地马拉', '几内亚比索': '几内亚比绍',
  '象牙海岸': '科特迪瓦', '肯亚': '肯尼亚', '吉里巴斯': '基里巴斯', '吉尔吉斯': '吉尔吉斯斯坦',
  '寮国': '老挝', '赖索托': '莱索托', '赖比瑞亚': '利比里亚', '马拉威': '马拉维',
  '马尔地夫': '马尔代夫', '马利': '马里', '茅利塔尼亚': '毛里塔尼亚', '模里西斯': '毛里求斯',
  '莫三比克': '莫桑比克', '诺鲁': '瑙鲁', '尼日': '尼日尔', '奈及利亚': '尼日利亚',
  '帛琉': '帕劳', '卡达': '卡塔尔', '卢安达': '卢旺达', '圣克里斯多福及尼维斯': '圣基茨和尼维斯',
  '圣露西亚': '圣卢西亚', '圣文森及格瑞那丁': '圣文森特和格林纳丁斯', '圣马利诺': '圣马力诺',
  '圣多美普林西比': '圣多美和普林西比', '塞西尔': '塞舌尔', '塞拉耶佛': '塞拉利昂',
  '索马利亚': '索马里', '苏利南': '苏里南', '史瓦济兰': '斯威士兰', '塔吉克': '塔吉克斯坦',
  '坦尚尼亚': '坦桑尼亚', '东加': '汤加', '突尼西亚': '突尼斯', '吐瓦鲁': '图瓦卢',
  '乌兹别克': '乌兹别克斯坦', '万那杜': '瓦努阿图', '叶门': '也门', '尚比亚': '赞比亚',
  '辛巴威': '津巴布韦', '印尼': '印度尼西亚',
};

// ---------- 4. 轮胎全值映射（仅 Game_Tyre_* 键） ----------
const tyreMap = {
  '冬天': '冬季胎', '雪地': '雪地胎', '干燥': '干胎', '街道': '街胎',
  '热熔胎': '光头胎', '硬质热熔胎': '硬光头胎', '软质热熔胎': '软光头胎',
  '全天气': '全天候', '职业': 'Pro',
};

// ---------- 5. 人工修正（优先于 all_entries 的台式译文） ----------
const curated = {
  // 严重误译
  'Presence_Presence_LifetimeGoals': '终身目标',
  'Career_InvitationUnlockCriteria_HTC2UKTrophy': '跑出 5 个生涯最佳排位成绩',
  'Career_SessionInfoTypes_Testing': '测试赛',
  'Career_ChampionshipNames_SCLitesUK': '跑车轻量级英国锦标赛',
  'Career_InvitationUnlockCriteria_SupercarTrinityTrophy': '赢得印地赛车锦标赛即可解锁此邀请赛事。',
  'Career_NewsCrashes_nc04': '[TEAM] 的 [PLAYER] 在 [MOTORSPORT] 的 [LOCATION] 发生撞车，遗憾离场。',
  'Career_MotorsportQuickGuide_FasterJokerLapTitle': '回合赛制与规则——高速小丑圈',
  'Splash_Loading_PRE': '出品',
  'Splash_Loading_A': '一部',
  'Splash_Loading_CRE': '力作',
  'Splash_Loading_DIS': '发行',
  'Splash_Loading_Loading2': '正在加载',
  'Game_Legal_PRE': '出品',
  // 线上
  'Online_Nynp_RemovedFromGame': '你已被移出比赛',
  'Online_MultiplayerMenus_GROUPMATCHING': '组队匹配',
  'Online_MultiplayerMenus_HasLeftAsTheyGotStuck': '[USER] 因卡住而离开',
  'Online_Chat_No': '未找到相关结果',
  'Online_Chat_Inv3': '邀请入队',
  'Online_Chat_Inv4': '邀请入队',
  'Online_MultiplayerMenus_AlreadyInSearch': '正在搜索中',
  'Online_MultiplayerMenus_LookingForGamesToJoin': '正在寻找可加入的多人比赛',
  'Online_MultiplayerMenus_FailedToCreateAGame': '创建房间失败。',
  'Online_MultiplayerMenus_GameDisconnectedUserStu': '与游戏的连接超时。',
  'Online_Nynp_UserBanned': '你的账号已被封禁。请联系客服。',
  'Online_MultiplayerMenus_FailedToConnectDenied': '您的账户权限不足，目前无法使用此功能。',
  // Pit 工程师语音
  'Pit_Engineer_MotivationalA16': '我们今天很有机会跑出好成绩。来吧，全力冲刺！',
  'Pit_Engineer_FinalLapA11c': '最后一圈，这是你的最后一圈。稳住，把胜利带回家！',
  'Pit_Engineer_BackMarkerLeaderA303': '你即将套圈慢车——尽量干净利落地超过去。',
  'Pit_Engineer_BackMarkerSecondPlaceA302': '前方有慢车阻挡——看看有没有机会追近头车。',
  'Pit_Spotter_Slipstream2b': '后车正在吃你的尾流。小心。',
  'Pit_Engineer_AvoidLockupsA12a': '你的车轮有点抱死，可以试着调整一下刹车平衡。',
  'Pit_Engineer_GreenFlagA2': '绿旗！绿旗！绿旗！冲冲冲！',
  'Pit_Engineer_PitReleaseA8a': '放行。走！',
  'Pit_Engineer_PitReleaseA7i': '全部清空。出发吧。',
  'Pit_Strategy_TyresAllWeather': '全天候',
  'Pit_Spotter_ThreeWideOutside3': '两辆车在你的外侧。',
  // RAC
  'RAC_HUD_WarningWrongWay': '逆行',
  'RAC_HUD_SevereDamage': '严重损坏',
  'RAC_HUD_PersonalBest': '个人最好成绩',
  'RAC_UI_LookBack': '回头看',
  'RAC_UI_Sea4': '座椅升高',
  'RAC_UI_IcmActivate': '车内管理',
  'RAC_UI_GearTypeSpeed': '挡',
  'RAC_UI_Gears': '挡位',
  // Game HUD
  'Game_HUD_WarningWrongWay': '逆行',
  'Game_HUD_TyresTempCold': '升温中',
  'Game_HUD_SessionOverMessageEditorName': '冷却圈消息',
  'Game_HUD_PitBoardEditorName': '进站提示板',
  'Game_HUD_SplitTimeToFastestLap': '与最快圈的分段差',
  'Game_HUD_WarningUnsportsmanlikeConduct': '违反体育道德',
  'Game_HUD_Sector2Information': '分段 2 时间：[TIME]',
  // Game 按钮 / 菜单
  'Game_Buttons_Flavour': '风格',
  'Game_Buttons_Combo': '组合！',
  'Game_Buttons_Aggressive': '激进',
  'Game_InGameMenu_TrySettings': '试用设置',
  'Game_InGameMenu_3rdPlace': '第 3 名',
  'Game_InGameMenu_OrbitCamera': '环绕视角',
  'Game_InGameMenu_Volume': '音量',
  'Game_UI_SetupDescriptionLower': '调校描述',
  'Game_UI_FocalLength': '焦距',
  'Game_MainMenu_SaveOverExistingSetu': '覆盖现有调校存档位',
  'Game_TuningScreen_WarningOverwriteSlot': '确定要覆盖该调校存档位吗？',
  'Game_TuningScreen_HotLap': '飞行圈',
  'Game_MainMenu_PlayerGridPosition': '玩家发车位置',
  'Game_MainMenu_YourHighestFinish': '个人最高完赛名次',
  'Game_MainMenu_ToggleCommentaryOnOf': '切换解说 开/关',
  'Game_MainMenu_NoPasswordSet1': '未设置密码',
  'Game_MainMenu_WatchEsportsEventsCu': '观看正在直播的电竞赛事',
  'Game_MainMenu_LiveBroadcast': '直播',
  'Game_Monitor_Position': '名次：',
  'Game_Monitor_CountdownTimer': '倒计时器',
  'Game_Monitor_Hood': '引擎盖',
  'Game_Monitor_Chase': '追尾视角',
  'Game_Monitor_SessionLapsRemaining': '本节剩余圈数',
  'Game_Monitor_Broadcast': '直播',
  'Game_TimeTrialScreens_UseBestInSession': '使用本节最佳',
  'Game_TuningSetups_Stable': '稳定',
  'Game_TuningSetups_StableSpeedway': '椭圆赛道（稳定）',
  'Game_TuningSetups_StableCircuit': '赛道（稳定）',
  'Game_TuningSetups_StableOval': '椭圆赛道（稳定）',
  'Game_TuningSetups_StableDaytona': 'Daytona（稳定）',
  'Game_CommunityEvents_959ZolderBattle': '959 Zolder 对决',
  'Game_CommunityEvents_Group6Battle': '6 组对决',
  'Game_CommunityEvents_BattleItOutWithTheGr': '与 6 组级别一决高下，看看谁是最快的赛车和车手。',
  // 登录
  'Game_SignIn_NoDetails': '用户名或密码未输入。请重启游戏并输入 WMD 论坛登录信息。',
  'Game_SignIn_InsufficientAccess': '你的账号没有运行当前游戏的权限，请到 WMD 网站注册所需会员。',
  'Game_SignIn_ErrorBoxTitle': '登录错误！游戏即将退出。',
  'Game_SignIn_Maintenance': '服务器正在维护中。请查看 WMD 网站或稍后再试。',
  'Game_SignIn_ConcurrentUse': '无法登录，你的账号可能已在其他设备上登录，请等待 [MM] 分钟后再试。',
  'Game_SignIn_SyncError': '服务器/客户端同步错误！即将退出游戏。',
  'Game_SignIn_TrialTimeExpired': '免费试用已结束。如需继续游玩《Project CARS 2》，请访问 wmdportal.com 了解会员注册详情。',
  'Game_SignIn_TrialHeader': '试玩模式',
  // 帮助文本全文重写（源数据截断）
  'Game_HelpText_OptionsSystemUseSharedMemory': '"使用共享内存"用于选择是否允许游戏与随游戏运行的外部应用程序连接，以及使用哪个版本的外部应用程序。如果你没有使用任何外部应用程序，请将其设为"关闭"。如果你要使用的外部应用程序是为 Project CARS 开发的，请将其设为"Project CARS 1"；如果是为 Project CARS 2 开发的，请将其设为"Project CARS 2"。',
  'Game_HelpText_OptionsControlsControllerDamping2': '控制器阻尼用于调整从左向右或从右向左的转向速度。数值越低，左右转向越快；数值越高，转向越慢。',
  'SetupEngineer_Solutions_NotStoppingBiasRearMod': '将刹车平衡向后调整，从当前的 [INITIAL1]/[INITIAL2]（前/后）改为 [FINAL1]/[FINAL2]。',
  // 预设/默认与换挡帮助
  'Game_UI_SET': '调校与策略',
  'Pit_Strategy_Default': '默认',
  'RAC_UI_Default': '默认',
  'Game_HelpText_OptionsControlsInvertedGearing': '反转换挡适合对预设控制器配置满意、但希望互换升挡和降挡按钮的车手使用。',
  'Game_HelpText_OptionsControlsGearing': '换挡方式可选择自动或手动。手动挡可让你完全掌控升挡与降挡。选择自动挡时，车载电脑会在需要时自动为你换挡。',
  'Game_MainMenu_ByDefaultYourRaceWee': '默认情况下，你的比赛周末始终包含一场正赛。但你也可以按需添加若干练习赛或排位赛，启用后即可将其加入赛事，并自由调整设置。',
  'Game_MainMenu_ByDefaultYourRaceWee1': '默认情况下，你的比赛周末始终包含一场正赛。但你也可以按需添加练习赛或排位赛，启用后即可将其加入赛事，并自由调整设置。',
  'Game_Tutorials1stTime_SessionSettings': '在"赛程设置"中，你可以为自定义赛事启用或停用练习赛和/或排位赛。你还可以在这里配置练习赛和排位赛的时长、游戏内开始时间、时间推进和天气设置。',
  // 车辆详情
  'VehicleDetails_VehicleDetails_F5': 'F5',
  'VehicleDetails_VehicleDetails_EngineV8': 'V8 引擎',
  'VehicleDetails_VehicleDetails_EngineV4': 'V4 引擎',
  'VehicleDetails_VehicleDetails_VintageGT': '经典 GT',
  'VehicleDetails_VehicleDetails_HistoricTouring2': '经典房车 2 组',
  'VehicleDetails_VehicleDetails_VintageF1A': '经典一级方程式 A 组',
  'VehicleDetails_VehicleDetails_VintagePrototypeGT1': '经典原型 GT1 组',
  // General
  'General_TimeDateCurrency_LengthFormatMetres': '[LENGTH] 米',
  'General_TimeDateCurrency_PlayTimeFormatDDHHMM': '[DD]天 [HH]小时 [MM]分',
  'General_TrackDetails_RuapunaParkACircuit': 'Ruapuna Park A 赛道',
  'General_TrackDetails_MercedesBenzDrivingEventsIceTrackFull': 'Mercedes-Benz 驾驶活动冰雪赛道（全程）',
  // Platform
  'Platform_ControllerPS3_ShifterForward': '升挡',
  // 圈型用语
  'Game_UI_War': '热身圈',
  'Game_UI_War2': '热身赛：',
  'Game_RaceModes_Test': '热身赛',
  'Game_RaceModes_TestCaps': '热身赛',
  // Voiceover
  'Game_Voiceover_3': '3！',
  'Game_Voiceover_2': '2！',
  'Game_Voiceover_1': '1！',
  'Game_Voiceover_GO': '出发！',
  'Game_Voiceover_Get': '准备',
  'Game_Voiceover_To': '点燃',
  'Game_Voiceover_You3': '你的',
  'Game_Voiceover_Eng': '引擎',
  'Game_Voiceover_You': '你有一条新消息……',
  'Game_Voiceover_You2': '你有新消息……',
  'Game_Voiceover_Con': '恭喜！你赢得了一项荣誉！',
  'Game_Voiceover_Con2': '恭喜！你解锁了一项赞誉！',
  'Game_Voiceover_Con3': '恭喜！你达成了"零到英雄"生涯目标！',
  'Game_Voiceover_Con4': '恭喜！你达成了"卫冕冠军"生涯目标！',
  'Game_Voiceover_Con5': '恭喜！你达成了"三冠王"生涯目标！',
  'Game_Voiceover_Con6': '恭喜！你已证明自己有资格与其他赛车传奇一同进入名人堂！',
  'Game_Voiceover_Wel': '欢迎来到车手网络',
  'Game_Voiceover_Pow': '由车手网络驱动',
  'Game_Voiceover_Fol': '在 Twitter 上关注我们 - @WMDCars',
  'Game_Voiceover_Fol2': '在 Instagram 上关注我们 - @projectcarsgame',
  'Game_Voiceover_Pre': '立即预订',
  'Game_Voiceover_Fro': '来自打造 GTR 和 SHIFT 系列的团队……',
  'Game_Voiceover_Pro': 'Project CARS —— 终极车手之旅',
  'Game_Voiceover_Pro2': 'Project CARS —— 车手打造，为车手而生',
  'Game_Voiceover_Pro3': 'Project CARS —— 相信这股热潮',
  'Game_Voiceover_Pro4': 'Project CARS —— 点燃你的引擎',
  'Game_Voiceover_Pro5': 'Project CARS —— 超越现实',
  'Game_Voiceover_Pro6': 'Project CARS —— 一段旅程，一个终点',
  'Game_Voiceover_Pro8': 'Project CARS —— 即将推出',
  'Game_Voiceover_By': '车手打造，为车手而生',
};

// ---------- 6. 按键名修正圈型用语 ----------
function keyAware(key, val) {
  if (/formation/i.test(key)) val = val.replace(/暖胎圈/g, '编队圈');
  if (/warm/i.test(key)) val = val.replace(/暖胎圈：/g, '热身赛：').replace(/暖胎圈/g, '热身圈');
  if (/hot\s?lap/i.test(key)) val = val.replace(/暖胎圈/g, '飞行圈');
  return val;
}

function convert(key, val, table) {
  if (typeof val !== 'string' || !val) return val;
  for (const [f, r] of termDict) val = val.split(f).join(r);
  for (const [re, r] of regexRules) val = val.replace(re, r);
  if (countryMap[val]) val = countryMap[val];
  if (table === 'Game' && key.startsWith('Game_Tyre_') && tyreMap[val]) val = tyreMap[val];
  return keyAware(key, val);
}

// ---------- 合并 ----------
const existingGlobal = new Set();
for (const t of Object.keys(existing)) for (const k of Object.keys(existing[t])) existingGlobal.add(k);

const tableOrder = ['Game', 'General', 'Pit', 'Platform', 'Presence', 'RAC',
  'Career', 'ChatFilter', 'Credits', 'Drivers', 'Online', 'SetupEngineer', 'Splash', 'VehicleDetails'];
const extraTables = [...new Set(all.map(e => e.table))].filter(t => !tableOrder.includes(t));
tableOrder.push(...extraTables);

const out = {};
const report = [];
let statExistingKept = 0, statExistingAdjusted = 0, statCuratedApplied = 0, statCuratedSkipped = 0, statConverted = 0;

for (const t of tableOrder) out[t] = {};
for (const t of tableOrder) {
  for (const e of all.filter(x => x.table === t)) {
    const k = e.key;
    if (existing[t] && Object.prototype.hasOwnProperty.call(existing[t], k)) {
      const before = existing[t][k];
      const after = convert(k, before, t);
      if (before !== after) { statExistingAdjusted++; report.push(`[existing-adjust] ${t}/${k}\n  旧: ${before}\n  新: ${after}`); }
      else statExistingKept++;
      out[t][k] = after;
    } else if (Object.prototype.hasOwnProperty.call(curated, k)) {
      out[t][k] = curated[k];
      statCuratedApplied++;
    } else {
      out[t][k] = convert(k, e.chinese, t);
      statConverted++;
    }
  }
}

// existing 独有条目（不在 all_entries 中的 45 条）
let statExtraKept = 0, statExtraAdjusted = 0;
for (const t of Object.keys(existing)) {
  if (!out[t]) out[t] = {};
  for (const k of Object.keys(existing[t])) {
    if (!all.find(x => x.key === k)) {
      const before = existing[t][k];
      const after = convert(k, before, t);
      if (before !== after) { statExtraAdjusted++; report.push(`[extra-adjust] ${t}/${k}\n  旧: ${before}\n  新: ${after}`); }
      else statExtraKept++;
      out[t][k] = after;
    }
  }
}

// curated 键是否命中 existing（提示复核）
for (const k of Object.keys(curated)) {
  if (existingGlobal.has(k)) { statCuratedSkipped++; report.push(`[curated-skipped] ${k} 已存在人工译文，未覆盖`); }
}

const total = Object.values(out).reduce((s, t) => s + Object.keys(t).length, 0);
console.log('=== 统计 ===');
console.log('沿用现有译文(未变):', statExistingKept);
console.log('现有译文术语统一(已变):', statExistingAdjusted);
console.log('独有条目(未变/已变):', statExtraKept, '/', statExtraAdjusted);
console.log('人工修正应用:', statCuratedApplied, ' 跳过(已有译文):', statCuratedSkipped);
console.log('词典转换条目:', statConverted);
console.log('输出总条目:', total);
for (const t of tableOrder) console.log(' ', t, Object.keys(out[t]).length);

if (!DRY) {
  fs.writeFileSync(path.join(DIR, 'translations.json'), JSON.stringify(out, null, 2) + '\n', 'utf8');
  console.log('已写入 translations.json');
} else {
  console.log('[dry-run] 未写入文件');
}
if (report.length) {
  fs.writeFileSync(path.join(DIR, 'convert_report.txt'), report.join('\n\n'), 'utf8');
  console.log('变更报告:', report.length, '条 -> convert_report.txt');
}
