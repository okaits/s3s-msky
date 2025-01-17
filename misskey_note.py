""" Note to misskey """
import json
import dateutil.parser as dateparser
import dateutil.tz as datetz
import misskey  # pylint: disable=E0401
import os
from time import sleep

if os.name == 'nt':
    import locale
    locale.setlocale(locale.LC_CTYPE, "Japanese_Japan.932")

salmon_sp_codes = {"Triple Inkstrike": "トリプルトルネード", "Crab Tank": "カニタンク", "Booyah Bomb": "ナイスダマ", "Killer Wail 5.1": "メガホンレーザー5.1ch", "Inkjet": "ジェットパック", "Reefslider": "サメライド", "Wave Breaker": "ホップソナー"}
salmon_rate_codes = {"Apprentice": "かけだし", "Part-Timer": "はんにんまえ", "Profreshional": "たつじん", "Profreshional +1": "たつじん +1", "Profreshional +2": "たつじん +2", "Profreshional +3": "たつじん +3", "Go-Getter": "いちにんまえ", "Overachiver": "じゅくれん", "Eggsecutive VP": "でんせつ"}
salmon_event_wave_codes = {"Rush": "ヒカリバエ（ラッシュ）", "Goldie Seeking": "金シャケ探し", "The Griller": "グリル", "The Mothership": "ハコビヤ襲来", "Fog": "霧", "Cohock Charge": "ドスコイの群れ", "Giant Tornado": "竜巻", "Mudmouth Eruptions": "ドロシャケ"}
salmon_gametype_codes = {"REGULAR": "通常", "TEAM_CONTEST": "バイトチームコンテスト", "BIG_RUN": "ビッグラン"}

class Module():
    """ Initial class """
    def __init__(self):
        print("Loaded module: misskey_note")
        self.name = "misskey_note"
        try:
            with open(f"{os.path.dirname(__file__)}/misskey.json", encoding="utf-8") as conf:
                confdict = json.load(conf)
            try:
                self.server = confdict["server"]
                self.api_token = confdict["api_token"]
            except KeyError:
                print("Couldn't read config file. Re-creating it...")
                self._create_config()
        except FileNotFoundError:
            print("Couldn't find config file. Creating it...")
            self._create_config()
        self.api = misskey.Misskey(address=self.server, i=self.api_token)
        print(f"[misskey_note] Logged in as: {self.api.i()['name']}\n")

    def pre(self, result):
        pass

    def post(self, data: list, url: str):
        """ Note to misskey server """

        if "vsHistoryDetail" in data[0]["data"]:
            data = data[0]["data"]["vsHistoryDetail"]
            #print(json.dumps(data)) #DEBUG
            time = dateparser.isoparse(data["playedTime"]).astimezone(tz=datetz.gettz("Asia/Tokyo")).strftime("%Y/%m/%d %H:%M:%S JST (24時間表記)")
            gametype = data["vsRule"]["name"]
            mode = data["vsMode"]["mode"]
            my_color = f"{str(int(data['myTeam']['color']['r']*100))}{str(int(data['myTeam']['color']['g']*100))}{str(int(data['myTeam']['color']['b']*100))}"
            enemy_color = []
            for enemy in data['otherTeams']:
                enemy_color.append(f"{str(int(enemy['color']['r']*100))}{str(int(enemy['color']['g']*100))}{str(int(enemy['color']['b']*100))}")
            if mode == "LEAGUE":
                gametype = f"{gametype} (イベントマッチ)"
                leaguepower = data["leagueMatch"]["myLeaguePower"]
                leagueevent = data["leagueMatch"]["leagueMatchEvent"]["name"]
            if mode == "FEST":
                gametype = f"{gametype} (フェス)"
                contribution = data["festMatch"]["contribution"]
                festteam = data["myTeam"]["festTeamName"]
                festpower = data["festMatch"]["myFestPower"]
                if festpower == None:
                    festpower = 0
            if data["vsRule"]["rule"] == "TRI_COLOR":
                #TODO
                raise Exception("Not implemented.")
            try:
                for player in data["myTeam"]["players"]:
                    if player["isMyself"] is True:
                        me = player
                try:
                    kills = me["result"]["kill"]
                    assists = me["result"]["assist"]
                    deaths = me["result"]["death"]
                    specials = me["result"]["special"]
                    weapon = me["weapon"]["name"]
                    points = me["paint"]
                except TypeError:
                    # Maybe disconnected
                    kills = 0
                    assits = 0
                    deaths = 0
                    specials = 0
                    weapon = 0
                    points = 0
            except KeyError:
                me = {}
                kills = 0
                assists = 0
                deaths = 0
                specials = 0
            if data["judgement"] == "WIN":
                judgement = True
                disconnected = False
                exempted=False
            elif data["judgement"] == "LOSE":
                judgement = False
                disconnected = False
                exempted = False
            elif data["judgement"] == "DEEMED_LOSE":
                judgement = False
                disconnected = True
                exempted = False
            elif data["judgement"] == "DRAW":
                judgement = None
                disconnected = True
                exempted=False
            elif data["judgement"] == "EXEMPTED_LOSE":
                judgement = False
                disconnected = False
                exempted = True
            if data["myTeam"]["result"] is not None:
                if gametype.startswith("ナワバリバトル"):
                    judge_good_guys = str(round(data["myTeam"]["result"]["paintRatio"] * 100, 2)) + "%"
                    judge_bad_guys = str(round(data["otherTeams"][0]["result"]["paintRatio"] * 100, 2)) + "%"
                else:
                    judge_good_guys = str(data["myTeam"]["result"]["score"]) + "カウント"
                    judge_bad_guys = str(data["otherTeams"][0]["result"]["score"]) + "カウント"
            stage = data["vsStage"]["name"]
            header = "Splatoon3: バトル結果\n"
            msg = f"日時: **{time}**\n"
            msg += f"種別: **{gametype}**\n"
            if judgement is True:
                msg += "結果: $[fg.color=ff0000 **勝利**]\n"
            elif judgement is False and disconnected is False and exempted is False:
                msg += "結果: $[fg.color=0000ff **敗北**]\n"
            elif judgement is None:
                msg += "結果: $[fg.color=00ff00 **引き分け**]\n"
            elif judgement is False and disconnected is True:
                msg += "結果: **敗北**<small>（切断）</small>\n"
            elif judgement is False and exempted is True:
                msg += "結果: **敗北**<small>（免除）</small>\n"
            msg += f"ステージ: **{stage}**\n"
            if disconnected is False or judgement is True:
                msg += f"塗りポイント: **{points}**\n"
                msg += f"ブキ: **{weapon}**\n"
                if judge_good_guys == "100カウント":
                    msg += f"ジャッジ: $[fg.color={my_color} **ノックアウト！**]\n"
                elif judge_bad_guys == "100カウント":
                    msg += f"ジャッジ: $[fg.color={enemy_color[0]} **ノックアウト！**]\n"
                else:
                    msg += f"ジャッジ: $[fg.color={my_color} **{judge_good_guys}**] 対 $[fg.color={enemy_color[0]} **{judge_bad_guys}**]\n"
                msg += f'キル数: **{kills}**\n'
                msg += f'アシスト数: **{assists}**\n'
                msg += f'デス数: **{deaths}**\n'
                msg += f'スペシャル使用数: **{specials}**\n'
            if mode == "FEST":
                msg += f"フェス陣営: $[fg.color={my_color} **{festteam}**]\n"
                msg += f"貢献度: **{contribution}**\n"
                msg += f"フェスパワー: **{festpower}**\n"
            if mode == "LEAGUE":
                msg += f"イベントパワー: **{leaguepower}**\n"
                msg += f"参加イベント: **{leagueevent}**\n"
            if disconnected is True and judgement is True:
                msg += "\n<small>対戦相手/味方が切断したため、負けとしてカウントされませんでした。</small>"
            elif disconnected is True and judgement is False:
                msg += "\n**自分が切断したため、負けとしてカウントされました。**"
            elif judgement is None:
                msg += "\n**対戦相手/味方が開始一分以内に切断したため、無効試合となりました。**"
            elif exempted is True:
                msg += "\n<small>対戦相手/味方が切断したため、敗北が免除されました。</small>"
            if url is not None:
                msg += f"\n[バトル詳細はこちら]({url})"
            while True:
                try:
                    self.api.notes_create(text=msg, cw=header)
                except misskey.exceptions.MisskeyAPIException:
                    sleep(10)
                    continue
                else:
                    break
            #print(msg)
        elif "coopHistoryDetail" in data[0]["data"]:
            data = data[0]["data"]["coopHistoryDetail"]
            #print(data) #DEBUG
            time = dateparser.isoparse(data["playedTime"]).astimezone(tz=datetz.gettz("Asia/Tokyo")).strftime("%Y/%m/%d %H:%M:%S JST (24時間表記)")
            gametype = salmon_gametype_codes[data["rule"]]
            danger = data["dangerRate"]
            special = salmon_sp_codes[data["myResult"]["specialWeapon"]["name"]]
            try:
                afterrate = salmon_rate_codes[data["afterGrade"]["name"]] + " " + str(data["afterGradePoint"])
            except TypeError:
                afterrate = "-"
            waves = {}
            alleggs = 0
            for wave in data["waveResults"]:
                waves[wave["waveNumber"]] = {}
                waves[wave["waveNumber"]]["wave"] = wave["waveNumber"]
                waves[wave["waveNumber"]]["ikura_norms"] = wave["deliverNorm"]
                waves[wave["waveNumber"]]["ikura_number"] = wave["teamDeliverCount"]
                if wave["teamDeliverCount"] is not None:
                    alleggs += wave["teamDeliverCount"]
                if wave["eventWave"] is not None:
                    waves[wave["waveNumber"]]["event"] = salmon_event_wave_codes[wave["eventWave"]["name"]]
                elif data["bossResult"] is not None and data["bossResult"]["hasDefeatBoss"] is True and wave["waveNumber"] == 4:
                    waves[wave["waveNumber"]]["event"] = "オカシラ襲来$[fg.color=00ff00 $[shake （討伐成功）]]"
                    waves[wave["waveNumber"]]["ikura_norms"] = None
                    waves[wave["waveNumber"]]["ikura_number"] = None
                elif data["bossResult"] is not None and wave["waveNumber"] == 4:
                    waves[wave["waveNumber"]]["event"] = "オカシラ襲来$[fg.color=ff0000 （討伐失敗）]"
                    waves[wave["waveNumber"]]["ikura_norms"] = None
                    waves[wave["waveNumber"]]["ikura_number"] = None
                else:
                    waves[wave["waveNumber"]]["event"] = "通常"
                if data["resultWave"] == wave["waveNumber"]:
                    if wave["deliverNorm"] < wave["teamDeliverCount"]:
                        waves[wave["waveNumber"]]["failedreason"] = "全滅"
                    else:
                        waves[wave["waveNumber"]]["failedreason"] = "納品不足または全滅"
            if data["resultWave"] == 0:
                failed = False
                disconnected = False
                if data["rule"] == "TEAM_CONTEST":
                    waves_num = 5
                elif 4 in waves:
                    waves_num = 4
                else:
                    waves_num = "3"
            elif data["resultWave"] < 0:
                failed = True
                disconnected = True
            else:
                failed = True
                waves_num = data["resultWave"]
                disconnected = False
            header = "Splatoon3: サーモンランNW バイト結果\n"
            msg = f"日時: **{time}**\n"
            msg += f"種別: **{gametype}**\n"
            msg += f"スペシャルウェポン: **{special}**\n"
            msg += f"終了後レート: **{afterrate}**\n"
            msg += f"キケン度: **{round(danger * 100, 1)}%**\n"
            if failed is True:
                msg += "結果: $[fg.color=ff7b00 **失敗**]\n"
            elif failed is False:
                msg += "結果: $[fg.color=00ff00 **成功**]\n"
            if alleggs >= 100:
                msg += f"合計納品数: $[fg.color=00ff00 $[shake **{alleggs}個**]]\n"
            if waves_num == 4 and data["rule"] != "TEAM_CONTEST":
                msg += "到達ウェーブ: $[shake **EX-WAVE**]\n"
            else:
                msg += f"到達ウェーブ: **WAVE{waves_num}**\n"
            for wave in waves.values():
                if wave["wave"] == 4 and data["rule"] != "TEAM_CONTEST":
                    msg += 'EX-WAVE:\n'
                else:
                    msg += f'WAVE{wave["wave"]}:\n'
                if wave["ikura_norms"] is not None:
                    msg += f'    ノルマ: **{wave["ikura_norms"]}個**\n'
                if wave["ikura_number"] is not None:
                    if wave["ikura_norms"] <= wave['ikura_number']:
                        msg += f'    納品数: $[fg.color=0000ff **{wave["ikura_number"]}個**] ($[fg.color=0000ff {round(int(wave["ikura_number"]) / int(wave["ikura_norms"]) * 100)}%])\n'
                    else:
                        msg += f'    納品数: $[fg.color=ff7b00 **{wave["ikura_number"]}個**] ($[fg.color=ff0000 {round(int(wave["ikura_number"]) / int(wave["ikura_norms"]) * 100)}%])\n'
                msg += f'    種別: **{wave["event"]}**\n'
                if wave["wave"] == waves_num and failed is True:
                    msg += f'    失敗理由: **{wave["failedreason"]}**\n'
            if disconnected is True:
                msg += "\n**自分が切断したため、WAVE1失敗としてカウントされました。**\n"
            if url is not None:
                msg += f"\n[バトル詳細はこちら]({url})"
            while True:
                try:
                    self.api.notes_create(text=msg, cw=header)
                except misskey.exceptions.MisskeyAPIException:
                    sleep(10)
                    continue
                else:
                    break
            #print(msg) #DEBUG


    def _create_config(self):
        """ Ask user to enter server URL and api key. """
        self.server = input("Misskey Server URL: ")
        auth = misskey.MiAuth(self.server, name="s3s with misskey", permission=["read:account", "write:notes"])
        print(f"Please login into your server here: {auth.generate_url()}")
        input("Press Enter to continue.")
        self.api_token = auth.check()
        with open(f"{os.path.dirname(__file__)}/misskey.json", "w", encoding="utf-8") as conf:
            conf.write(json.dumps({"server": self.server, "api_token": self.api_token}))
        print("Misskey server config done.")
        print("NOTE: Delete misskey.json to logout from your server.")
