""" Note to misskey """
import json
import dateutil.parser as dateparser
import dateutil.tz as datetz
import misskey  # pylint: disable=E0401

class Module():
    """ Initial class """
    def __init__(self):
        try:
            with open("misskey.json", encoding="utf-8") as conf:
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
                me = data["myTeam"]["players"][0]
                kills = me["result"]["kill"]
                assists = me["result"]["assist"]
                deaths = me["result"]["death"]
                specials = me["result"]["special"]
                weapon = me["weapon"]["name"]
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
            if disconnected is False or judgement is True:
                msg += f"ブキ: {weapon}\n"
                msg += f"ジャッジ: {judge_good_guys} 対 {judge_bad_guys}\n"
                msg += f'キル数: {kills}\n'
                msg += f'アシスト数: {assists}\n'
                msg += f'デス数: {deaths}\n'
                msg += f'スペシャル使用数: {specials}'
            if disconnected is True and judgement is True:
                msg += "\n対戦相手/味方が切断したため、負けとしてカウントされませんでした。"
            elif disconnected is True and judgement is False:
                msg += "\n自分が切断したため、負けとしてカウントされました。"
            #self.api.notes_create(text=msg)
            print(msg)
        elif "coopHistoryDetail" in data[0]["data"]:
            msg = "Splatoon3: バイト結果が検出されました。\n"
            # TODO
            raise Exception("Not implemented.")

    def _create_config(self):
        """ Ask user to enter server URL and api key. """
        self.server = input("Misskey Server URL: ")
        auth = misskey.MiAuth(self.server, name="s3s with misskey")
        print(f"Please login into your server here: {auth.generate_url()}")
        input("Press Enter to continue.")
        self.api_token = auth.check()
        with open("misskey.json", "w", encoding="utf-8") as conf:
            conf.write(json.dumps({"server": self.server, "api_token": self.api_token}))
