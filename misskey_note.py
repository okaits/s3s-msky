""" Note to misskey """
import json
import dateutil.parser as dateparser
import dateutil.tz as datetz
import misskey  # pylint: disable=E0401
import os

salmon_sp_codes = {"Triple Inkstrike": "トリプルトルネード", "Crab Tank": "カニタンク", "Booyah Bomb": "ナイスダマ", "Killer Wail 5.1": "メガホンレーザー5.1ch", "Inkjet": "ジェットパック", "Reefslider": "サメライド", "Wave Breaker": "ホップソナー"}
salmon_rate_codes = {"Apprentice": "かけだし", "Part-Timer": "はんにんまえ", "Profeshional": "たつじん", "Profeshional +1": "たつじん +1", "Profeshional +2": "たつじん +2", "Profeshional +3": "たつじん +3", "Go-Getter": "いちにんまえ", "Overachiver": "じゅくれん", "Eggsecutive VP": "でんせつ"}
salmon_event_wave_codes = {"Rush": "ヒカリバエ（ラッシュ）", "Goldie Seeking": "金シャケ探し", "The Griller": "グリル", "The Mothership": "ハコビヤ襲来", "Fog": "霧", "Cohock Charge": "ドスコイの群れ", "Giant Tornado": "竜巻", "Mudmouth Eruptions": "ドロシャケ"}
salmon_gametype_codes = {"GENERAL": "通常", "TEAM_CONTEST": "バイトチームコンテスト"}

class Module():
    """ Initial class """
    def __init__(self):
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

    def send(self, data: list):
        """ Note to misskey server """
        if "vsHistoryDetail" in data[0]["data"]:
            data = data[0]["data"]["vsHistoryDetail"]
            time = dateparser.isoparse(data["playedTime"]).astimezone(tz=datetz.gettz("Asia/Tokyo")).strftime("%Y/%m/%d %H:%M:%S JST (24時間表記)")
            gametype = data["vsRule"]["name"]
            if data["vsRule"]["rule"] == "TRI_COLOR":
                #TODO
                raise Exception("Not implemented.")
            try:
                for player in data["myTeam"]["players"]:
                    if player["isMyself"] is True:
                        me = player
                kills = me["result"]["kill"]
                assists = me["result"]["assist"]
                deaths = me["result"]["death"]
                specials = me["result"]["special"]
                weapon = me["weapon"]["name"]
                points = me["paint"]
            except KeyError:
                me = {}
                kills = 0
                assists = 0
                deaths = 0
                specials = 0
            if data["judgement"] == "WIN":
                judgement = True
                disconnected = False
            elif data["judgement"] == "LOSE":
                judgement = False
                disconnected = False
            elif data["judgement"] == "DEEMED_LOSE":
                judgement = False
                disconnected = True
            elif data["judgement"] == "DRAW":
                judgement = None
                disconnected = True
            if data["myTeam"]["result"] is not None:
                if gametype == "ナワバリバトル":
                    judge_good_guys = str(round(data["myTeam"]["result"]["paintRatio"] * 100, 2)) + "%"
                    judge_bad_guys = str(round(data["otherTeams"][0]["result"]["paintRatio"] * 100, 2)) + "%"
                else:
                    judge_good_guys = str(data["myTeam"]["result"]["score"]) + "カウント"
                    judge_bad_guys = str(data["otherTeams"][0]["result"]["score"]) + "カウント"
            stage = data["vsStage"]["name"]
            msg = "Splatoon3: バトルが検出されました。\n"
            msg += f"日時: {time}\n"
            msg += f"種別: {gametype}\n"
            if judgement is True:
                msg += "結果: 勝利\n"
            elif judgement is False and disconnected is False:
                msg += "結果: 敗北\n"
            elif judgement is None:
                msg += "結果: 引き分け\n"
            elif judgement is False and disconnected is True:
                msg += "結果: 敗北（切断）\n"
            msg += f"ステージ: {stage}\n"
            if disconnected is False or judgement is True:
                msg += f"塗りポイント: {points}\n"
                msg += f"ブキ: {weapon}\n"
                if judge_good_guys == "100" or judge_bad_guys == "100":
                    msg += "ジャッジ: ノックアウト！\n"
                else:
                    msg += f"ジャッジ: {judge_good_guys} 対 {judge_bad_guys}\n"
                msg += f'キル数: {kills}\n'
                msg += f'アシスト数: {assists}\n'
                msg += f'デス数: {deaths}\n'
                msg += f'スペシャル使用数: {specials}'
            if disconnected is True and judgement is True:
                msg += "\n対戦相手/味方が切断したため、負けとしてカウントされませんでした。"
            elif disconnected is True and judgement is False:
                msg += "\n自分が切断したため、負けとしてカウントされました。"
            elif judgement is None:
                msg += "\n対戦相手/味方が開始一分以内に切断したため、無効試合となりました。"
            self.api.notes_create(text=msg)
            #print(msg)
        elif "coopHistoryDetail" in data[0]["data"]:
            data = data[0]["data"]["coopHistoryDetail"]
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
                    waves[wave["waveNumber"]]["event"] = "オカシラ襲来（討伐成功）"
                    waves[wave["waveNumber"]]["ikura_norms"] = "n/a"
                    waves[wave["waveNumber"]]["ikura_number"] = "n/a"
                elif data["bossResult"] is not None and wave["waveNumber"] == 4:
                    waves[wave["waveNumber"]]["event"] = "オカシラ襲来（討伐失敗）"
                    waves[wave["waveNumber"]]["ikura_norms"] = "n/a"
                    waves[wave["waveNumber"]]["ikura_number"] = "n/a"
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
            msg = "Splatoon3: バイト結果が検出されました。\n"
            msg += f"日時: {time}\n"
            msg += f"種別: {gametype}\n"
            msg += f"スペシャルウェポン: {special}\n"
            msg += f"終了後レート: {afterrate}\n"
            msg += f"キケン度: {round(danger * 100, 1)}%\n"
            if failed is True:
                msg += "結果: 失敗\n"
            elif failed is False:
                msg += "結果: 成功\n"
            msg += f"合計納品数: {alleggs}個\n"
            msg += f"到達ウェーブ: {waves_num}\n"
            for wave in waves.values():
                msg += f'ウェーブ{wave["wave"]}:\n'
                msg += f'    ノルマ: {wave["ikura_norms"]}個\n'
                msg += f'    納品数: {wave["ikura_number"]}個\n'
                msg += f'    種別: {wave["event"]}\n'
                if wave["wave"] == waves_num and failed is True:
                    msg += f'    失敗理由: {wave["failedreason"]}\n'
            if disconnected is True:
                msg += "\n自分が切断したため、WAVE1失敗としてカウントされました。\n"
            self.api.notes_create(text=msg)
            #print(msg)


    def _create_config(self):
        """ Ask user to enter server URL and api key. """
        self.server = input("Misskey Server URL: ")
        auth = misskey.MiAuth(self.server, name="s3s with misskey")
        print(f"Please login into your server here: {auth.generate_url()}")
        input("Press Enter to continue.")
        self.api_token = auth.check()
        with open(f"{os.path.dirname(__file__)}/misskey.json", "w", encoding="utf-8") as conf:
            conf.write(json.dumps({"server": self.server, "api_token": self.api_token}))
        print("Misskey server config done.")
        print("NOTE: Delete misskey.json to logout from your server.")