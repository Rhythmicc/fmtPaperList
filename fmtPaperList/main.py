from QuickProject.Commander import Commander
from . import *

app = Commander(name, True)
driver = None


def _fmt(s, max_len):
    return "<br />".join([s[i : i + max_len] for i in range(0, len(s), max_len)])


def get_driver():
    global driver
    if driver is None:
        from selenium import webdriver

        driver = webdriver.Remote(
            command_executor=config.select("remote_url"),
            desired_capabilities=webdriver.DesiredCapabilities.CHROME,
        )
    return driver


@app.command()
def check_paper(paperUrl: str, _st=None):
    import requests

    try:
        meeting = ""
        _st.update("正在判断论文类型") if _st else None
        paperUrl = paperUrl.strip()
        res = requests.get(paperUrl)
        if res is None or res.status_code != 200:
            raise ValueError("无法访问论文网页")
        html = res.text
        is_ieee = "IEEE <em>Xplore</em>" in html
        is_acm = "ACM Digital Library" in html
        if not is_ieee and not is_acm:
            raise Exception("Not IEEE or ACM paper")
        html = requirePackage("bs4", "BeautifulSoup")(html, "html.parser")
        authors = {}
        if is_acm:
            _st.update("正在解析ACM类型论文") if _st else None
            title = html.find("h1", {"class": "citation__title"}).text.strip()
            time = (
                html.find("span", {"class": "CitationCoverDate"})
                .text.strip()
                .split()[-1]
            )
            meeting = (
                html.find("span", {"class": "epub-section__title"})
                .text.strip()
                .split()[0]
            )
            _authors = html.find_all("li", {"class": "loa__item"})
            for author in _authors:
                name = author.find("span", {"class": "loa__author-name"})
                name = name.find("span").text
                unit = author.find("span", {"class": "loa_author_inst"})
                if unit is not None:
                    unit = unit.find("p").text
                else:
                    unit = "未知"
                authors[name] = unit
        if is_ieee:
            _st.update("正在解析IEEE类型论文") if _st else None
            from selenium.webdriver.common.by import By

            driver = get_driver()
            driver.get(paperUrl)
            driver.implicitly_wait(3)
            title = driver.find_element(By.CLASS_NAME, "document-title").text
            meeting = driver.find_element(
                By.XPATH,
                '//*[@id="LayoutWrapper"]/div/div/div/div[3]/div/xpl-root/div/xpl-document-details/div/div[1]/div/div[2]/section/div[2]/div/xpl-document-abstract/section/div[2]',
            )
            meeting = (
                meeting.find_element(By.CLASS_NAME, "u-pb-1")
                .find_element(By.TAG_NAME, "a")
                .text.strip()
            )
            time = meeting.split()[0]
            meeting = meeting.split()[-1][1:-1]

            cur_url = driver.current_url
            driver.get(cur_url + "/authors#authors")
            driver.implicitly_wait(1)
            div = driver.find_element(
                By.CLASS_NAME,
                "accordion-body",
            )

            for _id, _ in enumerate(
                div.find_elements(By.CLASS_NAME, "authors-accordion-container")
            ):
                name = driver.find_element(
                    By.XPATH,
                    f'//*[@id="authors"]/div[{_id + 1}]/xpl-author-item/div/div[1]/div/div[1]/a/span',
                ).text
                unit = driver.find_element(
                    By.XPATH,
                    f'//*[@id="authors"]/div[{_id + 1}]/xpl-author-item/div/div[1]/div/div[2]/div',
                ).text
                authors[name] = unit
        QproDefaultConsole.print(authors, meeting)
        return authors, meeting, title, time

    except Exception as e:
        QproDefaultConsole.print(QproErrorString, repr(e))
        return {}, meeting, "", ""


@app.command()
def check_all():
    with open("dist/1.md", "r") as f:
        lines = f.readlines()[2:]
        lines = [line.strip() for line in lines]

    infos = []
    with QproDefaultConsole.status("正在处理") as st:
        for _id, line in enumerate(lines):
            st.update(f"正在解析第 {_id + 1} 行")
            line = line.strip("|")
            _, title, time, url = [i.strip() for i in line.split("|")]
            st.update(f'正在解析论文 "{title}" 的作者与会议信息')
            retries = 3
            while retries > 0:
                authors, meeting, _title, _time = app.real_call("checkPaper", url, st)
                if len(authors) > 0:
                    title = _title
                    time = _time
                    break
                retries -= 1
            if not authors:
                QproDefaultConsole.print(QproErrorString, f"论文 {title} 解析失败: {url}")
            infos.append(
                {
                    "meeting": meeting,
                    "authors": authors,
                    "title": title,
                    "url": url,
                    "time": int(time),
                }
            )
    infos = sorted(infos, key=lambda x: -x["time"])
    with open("dist/to.md", "w") as f:
        print("|序号|会议|作者|单位|论文题目|发表时间|讲解人|", file=f)
        print("|:---:|:---:|---|---|---|:---:|:---:|", file=f)
        for _id, info in enumerate(infos):
            authors = "<br />".join(list(info["authors"].keys()))
            units = "<br />".join(list(set(info["authors"].values())))
            print(
                f"|{_id + 1}|{info['meeting']}|{authors}|{units}|[{info['title']}]({info['url']})|{info['time']}| |",
                file=f,
            )


@app.command()
def format(max_len: int = 50):
    with open("dist/to.md", "r") as f:
        lines = f.readlines()[2:]
        lines = [line.strip().strip("|") for line in lines]

    with open("dist/to-2.md", "w") as f:
        print("|序号|会议|作者|单位|论文题目|发表时间|讲解人|", file=f)
        print("|:---:|:---:|---|---|---|:---:|:---:|", file=f)
        for line in lines:
            _id, meeting, authors, units, title, time, _ = line.split("|")
            units = [_fmt(i.strip(), max_len) for i in units.split("<br />")]
            units = "<br />".join(units)
            print(
                f"|{_id}|{meeting}|{authors.strip()}|{units}|{title.strip()}|{time}| |",
                file=f,
            )


def main():
    """
    注册为全局命令时, 默认采用main函数作为命令入口, 请勿将此函数用作它途.
    When registering as a global command, default to main function as the command entry, do not use it as another way.
    """
    app()
    if driver is not None:
        driver.quit()


if __name__ == "__main__":
    main()
