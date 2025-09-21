# modules/ai_agent.py
# Sequential, LLM-assisted agent with graceful offline fallback
# Roman Urdu formal tone, normal free-form conversation supported.

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from config.settings import Config
from modules.utils import Logger
from modules.scraper import PakRailScraper

# Optional LLM (OpenRouter via OpenAI-compatible endpoint using LangChain)
try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None  # allow running without langchain_openai installed


class TrainBookingAI:
    """
    Sequential FSM:
      init -> from_city -> to_city -> date -> budget -> time -> confirm -> results_shown

    Features:
    - User free-form baat kare, agent locally parse karta hai
    - Agar local parsing se kuch naya na mile to (max 2 dafa) LLM se assist leni ki koshish
    - 429 / API fail par degrade_mode on ho jata hai (sirf local parsing par)
    - Roman Urdu formal tone; sawal ek ya do at a time
    """

    LLM_MAX_CALLS_PER_SESSION = 2

    def __init__(self):
        self.logger = Logger("TrainBookingAI")
        self.config = Config()

        self.state: Dict[str, Any] = {
            "stage": "init",
            "from_station": None,
            "to_station": None,
            "travel_date": None,     # YYYY-MM-DD
            "budget": None,          # "Economy Class" | "Business Class" | "AC Class" | "Rs. 3000"
            "preferred_time": None,  # "subah" | "dopahar" | "raat"
            "format_pref": None,     # optional: "table" | "list" | "json"
        }

        # LLM setup (optional)
        self.degrade_mode = False
        self.llm_calls = 0
        self.llm: Optional[Any] = None
        if ChatOpenAI and getattr(self.config, "OPENROUTER_API_KEY", None):
            try:
                self.llm = ChatOpenAI(
                    model=self.config.AI_MODEL,
                    temperature=0.3,
                    openai_api_key=self.config.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    timeout=18,
                )
            except Exception as e:
                self.logger.warning(f"LLM init failed, going offline: {e}")
                self.degrade_mode = True
        else:
            self.degrade_mode = True  # no LLM available

    # ---------------- Public API ----------------
    def process_user_input(self, user_input: str) -> str:
        try:
            txt = (user_input or "").strip()
            if not txt:
                return "Meharbani karke apna matlooba sawal ya maloomat likhein. 'reset' se naya start ho jaye ga."

            lw = txt.lower()
            if any(w in lw for w in ["reset", "restart", "fresh", "naya", "dobara"]):
                self.reset_conversation()
                self.state["stage"] = "from_city"
                return self._greet_intro()

            if any(w in lw for w in ["help", "madad", "kaise"]):
                return "Rehnumai: Bas seedhe alfaaz mein batayein. 'reset' se naya start. Ab current sawal ka jawab dein."

            # Soft reset if user starts brand-new route
            self._soft_reset_if_new_route(txt)

            # Try to ingest whatever user said (free-form)
            new_info = self._ingest(txt)

            # Stage machine
            st = self.state["stage"]

            if st == "init":
                # Respect parsed info even on first turn
                if self.state["from_station"] and self.state["to_station"]:
                    self.state["stage"] = "date"
                    return self._ask_date()
                if self.state["from_station"] and not self.state["to_station"]:
                    self.state["stage"] = "to_city"
                    return self._ask_to()
                if self.state["to_station"] and not self.state["from_station"]:
                    self.state["stage"] = "from_city"
                    return f"Destination note ho gaya: {self.state['to_station']}. Ab departure shehar batayein (misal: Islamabad)."
                # otherwise intro
                self.state["stage"] = "from_city"
                return self._greet_intro()

            if st == "from_city":
                if not self.state["from_station"]:
                    return self._nudge_from_city()

                if self.state.get("to_station"):
                    if str(self.state["to_station"]).lower() == str(self.state["from_station"]).lower():
                        self.state["to_station"] = None
                        return self._same_city_warning(self.state["from_station"])
                    self.state["stage"] = "date"
                    return self._ask_date()

                self.state["stage"] = "to_city"
                return self._ask_to()

            if st == "to_city":
                if self.state["to_station"] and self.state["from_station"]:
                    if str(self.state["to_station"]).lower() == str(self.state["from_station"]).lower():
                        return self._same_city_warning(self.state["from_station"])
                if not self.state["to_station"]:
                    return self._nudge_to_city()
                self.state["stage"] = "date"
                return self._ask_date()

            if st == "date":
                if not self.state["travel_date"]:
                    return self._nudge_date()
                if self._is_past(self.state["travel_date"]):
                    self.state["travel_date"] = None
                    return "Bara-e-meharbani mustaqbil ki date batayein (aaj/kal/parso ya YYYY-MM-DD)."
                self.state["stage"] = "budget"
                return self._ask_budget()

            if st == "budget":
                if not self.state["budget"]:
                    return self._nudge_budget()
                self.state["stage"] = "time"
                return self._ask_time()

            if st == "time":
                if not self.state["preferred_time"]:
                    return self._nudge_time()
                self.state["stage"] = "confirm"
                return self._confirm_message()

            if st == "confirm":
                if re.search(r"\b(haan|han|yes|ok|okay|ji|jee|search|proceed|start|kar)\b", lw):
                    return self._search_and_format()
                if re.search(r"\b(nahi|no|nahin|na)\b", lw):
                    # restart from beginning
                    self.state.update({
                        "from_station": None,
                        "to_station": None,
                        "travel_date": None,
                        "budget": None,
                        "preferred_time": None,
                    })
                    self.state["stage"] = "from_city"
                    return "Theek hai. Dobara shuru karte hain.\n" + self._greet_intro()
                # if user said more info in confirm stage, try to ingest and re-check
                if new_info and self._has_all_required(self.state):
                    return self._confirm_message()
                return "Meharbani karke tasdeeq karein: 'haan' likhein to main ab search shuru karun, warna 'nahi'."

            if st == "results_shown":
                if "reset" in lw:
                    self.reset_conversation()
                    self.state["stage"] = "from_city"
                    return self._greet_intro()
                return "Naya search karna ho to 'reset' likhein."

            # fallback
            self.state["stage"] = "from_city"
            return self._greet_intro()

        except Exception as e:
            self.logger.error(f"process_user_input error: {e}")
            return "Kuch masla aa gaya. 'reset' karke dobara koshish karein."

    def reset_conversation(self):
        self.state = {
            "stage": "init",
            "from_station": None,
            "to_station": None,
            "travel_date": None,
            "budget": None,
            "preferred_time": None,
            "format_pref": None,
        }
        self.degrade_mode = False
        self.llm_calls = 0

    # --------------- Soft reset when user starts a new route ---------------
    def _soft_reset_if_new_route(self, user_input: str):
        """
        If we are at the very start (init or from_city) and user mentions a new route
        (contains ' se ' or ' jana' or ' to ') and old from/to exist but are NOT
        mentioned in this message, clear old structured fields.
        """
        stage = self.state.get("stage")
        if stage not in ["init", "from_city"]:
            return
        lw = user_input.lower()

        looks_routey = (" se " in f" {lw} ") or (" jana" in lw) or (" to " in f" {lw} ")
        if not looks_routey:
            return

        old_from = (self.state.get("from_station") or "").lower()
        old_to = (self.state.get("to_station") or "").lower()

        if not (old_from or old_to):
            return  # nothing to clear

        mentions_old = False
        if old_from and old_from in lw:
            mentions_old = True
        if old_to and old_to in lw:
            mentions_old = True

        if not mentions_old:
            # clear stale fields but keep format_pref
            for k in ["from_station", "to_station", "travel_date", "budget", "preferred_time"]:
                self.state[k] = None

    # --------------- Ingestion (free-form) ---------------
    def _ingest(self, user_input: str) -> bool:
        """Local parse first; if nothing new & LLM allowed -> single JSON extract."""
        new_set = False

        # Route in one line: "karachi se lahore"
        fr, to = self._local_extract_route(user_input)
        if fr and not self.state["from_station"]:
            self.state["from_station"] = fr
            new_set = True
        if to and not self.state["to_station"]:
            self.state["to_station"] = to
            new_set = True

        # Individual fields
        if not self.state["from_station"]:
            c = self._local_extract_from_city(user_input)
            if c:
                self.state["from_station"] = c
                new_set = True

        if not self.state["to_station"]:
            d = self._local_extract_dest_city(user_input)
            if d:
                self.state["to_station"] = d
                new_set = True

        if not self.state["travel_date"]:
            dt = self._local_extract_date(user_input)
            if dt and not self._is_past(dt):
                self.state["travel_date"] = dt
                new_set = True

        if not self.state["preferred_time"]:
            t = self._local_extract_time(user_input)
            if t:
                self.state["preferred_time"] = t
                new_set = True

        if not self.state["budget"]:
            b = self._local_extract_budget(user_input)
            if b:
                self.state["budget"] = b
                new_set = True

        # Optional format preference
        if not self.state["format_pref"]:
            fmt = self._local_extract_format(user_input)
            if fmt:
                self.state["format_pref"] = fmt

        # If nothing new & LLM available -> single JSON parse attempt
        if (not new_set) and (not self.degrade_mode) and self.llm and self.llm_calls < self.LLM_MAX_CALLS_PER_SESSION:
            try:
                parsed = self._llm_extract(user_input)
                if parsed:
                    for k in ["from_station", "to_station", "travel_date", "budget", "preferred_time", "format_pref"]:
                        v = parsed.get(k)
                        if v and not self.state.get(k):
                            # guard date not past
                            if k == "travel_date" and self._is_past(v):
                                continue
                            self.state[k] = v
                            new_set = True
            except Exception as e:
                self.logger.warning(f"LLM extract failed -> offline: {e}")
                self.degrade_mode = True

        return new_set

    def _llm_extract(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Single JSON extraction call. Increases llm_calls. Raises on non-JSON to trigger offline."""
        self.llm_calls += 1
        today = datetime.now().strftime("%Y-%m-%d")
        sys = f"""
Aap Pakistani railway booking assistant hain. User ke free-form message se maloomat nikaalein.

Normalization:
- travel_date: YYYY-MM-DD (aaj={today}, kal=+1, parso=+2; past avoid)
- preferred_time: "subah"|"dopahar"|"raat" (sham/shaam/evening/night -> raat)
- budget: "Economy Class"|"Business Class"|"AC Class"|"Rs. <amount>"
- format_pref: "list"|"table"|"json" (optional)

Output ONLY JSON:
{{
  "from_station": null|"City",
  "to_station": null|"City",
  "travel_date": null|"YYYY-MM-DD",
  "budget": null|"Economy Class|Business Class|AC Class|Rs. 3000",
  "preferred_time": null|"subah|dopahar|raat",
  "format_pref": null|"list|table|json"
}}
"""
        prompt = f"{sys}\nUser message:\n{user_input}\n\nOutput ONLY the JSON object."

        resp = self.llm.invoke(prompt)
        # LangChain returns an AIMessage with .content
        content = getattr(resp, "content", None) or str(resp)
        data = self._safe_json_parse(content)
        if not data:
            raise RuntimeError("LLM non-JSON extraction")
        return data

    # --------------- Search + Format ---------------
    def _search_and_format(self) -> str:
        try:
            scraper = PakRailScraper()
            results = scraper.scrape_train_info(
                self.state["from_station"],
                self.state["to_station"],
                self.state["travel_date"],
                self.state["preferred_time"],
            )
            self.state["stage"] = "results_shown"

            d = self.state["travel_date"]
            try:
                d_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%d %B %Y (%A)")
            except Exception:
                d_fmt = d

            if not results:
                return (
                    "Is criteria par koi trains maujood nahi milin.\n\n"
                    f"Route: {self.state['from_station']} → {self.state['to_station']}\n"
                    f"Date: {d_fmt} | Time: {self.state['preferred_time']} | Budget: {self.state['budget']}\n\n"
                    "Bara-e-meharbani mukhtalif date/time try karein ya 'reset' likhein."
                )

            fmt = (self.state.get("format_pref") or "list").lower()
            if fmt == "json":
                return json.dumps({"results": results}, ensure_ascii=False, indent=2)
            if fmt == "table":
                return self._format_table(results, d_fmt)

            # default list
            lines = []
            lines.append("Zail mein uplabdh options darj hain:\n")
            lines.append(f"Route: {self.state['from_station']} → {self.state['to_station']}")
            lines.append(f"Date: {d_fmt} | Time: {self.state['preferred_time']} | Budget: {self.state['budget']}\n")
            for i, r in enumerate(results, 1):
                lines.append(
                    f"{i}. {r.get('name','Unknown')}\n"
                    f"   Waqt: {r.get('departure_time','-')} → {r.get('arrival_time','-')} ({r.get('duration','-')})\n"
                    f"   Fares: Economy {r.get('economy_fare','-')} | Business {r.get('business_fare','-')} | AC {r.get('ac_fare','-')}\n"
                    f"   Stops: {r.get('stops','-')}\n"
                )
            lines.append("\nNaye search ke liye 'reset' likhein. Kisi train ki tafseel chahiye ho to number batayein.")
            return "\n".join(lines)

        except Exception as e:
            self.logger.error(f"search error: {e}")
            return "Search ke dauran technical masla aa gaya. Bara-e-meharbani thori dair baad dobara koshish karein."

    # --------------- Tone / Prompts ---------------
    def _greet_intro(self) -> str:
        return "Assalam-o-Alaikum. Main aapki booking mein madad karunga. Pehle departure shehar batayein (misal: Karachi, Lahore, Islamabad)."

    def _ask_to(self) -> str:
        return f"Departure: {self.state['from_station']}. Ab meharbani kar ke destination shehar batayein."

    def _ask_date(self) -> str:
        fs = self.state['from_station']; ts = self.state['to_station']
        return f"Route set: {fs} → {ts}. Ab travel date batayein (aaj/kal/parso ya YYYY-MM-DD)."

    def _ask_budget(self) -> str:
        d = self.state["travel_date"] or ""
        try:
            d_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%d %B %Y (%A)")
        except Exception:
            d_fmt = d
        return f"Date confirm: {d_fmt}. Ab budget ya class preference batayein (Economy/Business/AC ya Rs. amount)."

    def _ask_time(self) -> str:
        return f"Budget confirm: {self.state['budget']}. Ab time preference batayein: subah, dopahar ya raat?"

    def _confirm_message(self) -> str:
        d = self.state["travel_date"] or ""
        try:
            d_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%d %B %Y (%A)")
        except Exception:
            d_fmt = d
        return (
            f"Summary:\n• Route: {self.state['from_station']} → {self.state['to_station']}\n"
            f"• Date: {d_fmt}\n"
            f"• Time: {self.state['preferred_time']}\n"
            f"• Budget: {self.state['budget']}\n\n"
            "Kya main ab search shuru karun? (haan/nahi)"
        )

    def _nudge_from_city(self) -> str:
        return "Bara-e-meharbani departure shehar batayein (misal: Karachi, Lahore)."

    def _nudge_to_city(self) -> str:
        return "Destination shehar batayein (e.g., Lahore, Quetta)."

    def _nudge_date(self) -> str:
        return "Date batayein — aaj/kal/parso ya specific (YYYY-MM-DD)."

    def _nudge_budget(self) -> str:
        return "Budget ya class preference batayein (Economy/Business/AC ya Rs. amount)."

    def _nudge_time(self) -> str:
        return "Time preference batayein: subah / dopahar / raat."

    def _same_city_warning(self, city: str) -> str:
        self.state["to_station"] = None
        return f"Departure aur destination ek hi shehar ({city}) nahi ho sakte. Bara-e-meharbani mukhtalif destination batayein."

    # --------------- Helpers: local parsing ---------------
    @staticmethod
    def _safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        t = str(text).strip()
        # strip potential leading 'json' and code fences
        t = re.sub(r'^\s*json\s*', '', t, flags=re.I).strip()
        t = re.sub(r'^\s*```(?:json)?\s*', '', t, flags=re.I)
        t = re.sub(r'\s*```\s*$', '', t)
        m = re.search(r'{.*}', t, flags=re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None

    @staticmethod
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "")).strip().lower()

    def _local_extract_route(self, text: str):
        t = self._norm(text)
        m = re.search(r"\b([a-z]{3,}(?:\s+[a-z]{3,})?)\s+se\s+([a-z]{3,}(?:\s+[a-z]{3,})?)\b", t)
        if m:
            fr = m.group(1).strip().split()[-1].title()
            to = m.group(2).strip().split()[-1].title()
            return fr, to
        return None, None

    def _local_extract_from_city(self, text: str):
        t = self._norm(text)
        # "... karachi se ..."
        m = re.search(r"\b([a-z]{3,}(?:\s+[a-z]{3,})?)\s+se\b", t)
        if m:
            return m.group(1).strip().split()[-1].title()
        # "from islamabad"
        m = re.search(r"\bfrom\s+([a-z]{3,}(?:\s+[a-z]{3,})?)\b", t)
        if m:
            return m.group(1).strip().split()[-1].title()
        # single token
        m = re.fullmatch(r"([a-z]{3,}(?:\s+[a-z]{3,})?)", t)
        if m:
            return m.group(1).strip().split()[-1].title()
        return None

    def _local_extract_dest_city(self, text: str):
        t = self._norm(text)
        # "... lahore jana ..."
        m = re.search(r"\b([a-z]{3,}(?:\s+[a-z]{3,})?)\s+jana\b", t)
        if m:
            return m.group(1).strip().split()[-1].title()
        # "to lahore"
        m = re.search(r"\bto\s+([a-z]{3,}(?:\s+[a-z]{3,})?)\b", t)
        if m:
            return m.group(1).strip().split()[-1].title()
        return None

    def _local_extract_date(self, text: str):
        t = self._norm(text)
        today = datetime.now()
        if "aaj" in t or "today" in t:
            return today.strftime("%Y-%m-%d")
        if "kal" in t or "tomorrow" in t:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        if "parso" in t or "day after" in t:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")

        # dd/mm/yyyy or dd-mm-yyyy
        m = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', t)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                dt = datetime(y, mo, d)
                if dt.date() >= today.date():
                    return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        # yyyy-mm-dd or yyyy/mm/dd
        m = re.search(r'\b(\d{4})[/-](\d{2})[/-](\d{2})\b', t)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                dt = datetime(y, mo, d)
                if dt.date() >= today.date():
                    return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        return None

    def _local_extract_time(self, text: str):
        t = self._norm(text)
        if any(k in t for k in ["subah", "morning", "fajr", "jaldi", "savere", "savera", "sawere"]):
            return "subah"
        if any(k in t for k in ["dopahar", "afternoon", "zuhr", "noon", "din", "day", "dopehar", "duphar", "dopehr"]):
            return "dopahar"
        if any(k in t for k in ["raat", "night", "late", "sham", "shaam", "evening", "maghrib", "shaam"]):
            return "raat"
        return None

    def _local_extract_budget(self, text: str):
        t = self._norm(text)
        # numeric amount
        m = re.findall(r'\b(\d{3,6})\b', t)
        if m:
            return f"Rs. {max(m)}"
        if re.search(r'\b(economy|sasta|cheap|budget)\b', t):
            return "Economy Class"
        if re.search(r'\b(business|biz)\b', t):
            return "Business Class"
        if re.search(r'\b(ac|a/c)\b', t) or "aircondition" in t or "air-conditioned" in t or "luxury" in t or "expensive" in t:
            return "AC Class"
        return None

    @staticmethod
    def _local_extract_format(text: str):
        t = re.sub(r"\s+", " ", (text or "")).strip().lower()
        if "table" in t:
            return "table"
        if "json" in t:
            return "json"
        if "list" in t:
            return "list"
        return None

    @staticmethod
    def _is_past(date_str: str) -> bool:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.date() < datetime.now().date()
        except Exception:
            return True

    @staticmethod
    def _has_all_required(s: Dict[str, Any]) -> bool:
        return all([
            bool(s.get("from_station")),
            bool(s.get("to_station")),
            bool(s.get("travel_date")),
            bool(s.get("preferred_time")),
            bool(s.get("budget")),
        ])

    def _format_table(self, results, date_fmt):
        def pad(s, n):
            s = str(s or "")
            return s[:n].ljust(n)

        lines = []
        header = f"{self.state.get('from_station')} → {self.state.get('to_station')} | {date_fmt} | {self.state.get('preferred_time')} | {self.state.get('budget')}"
        lines.append(header)
        lines.append("-" * 110)
        lines.append(f"{pad('No',3)} {pad('Train',22)} {pad('Depart',8)} {pad('Arrive',8)} {pad('Economy',12)} {pad('Business',12)} {pad('AC',10)} {pad('Stops',8)}")
        lines.append("-" * 110)
        for i, r in enumerate(results, 1):
            lines.append(
                f"{pad(i,3)} {pad(r.get('name','-'),22)} {pad(r.get('departure_time','-'),8)} {pad(r.get('arrival_time','-'),8)} "
                f"{pad(r.get('economy_fare','-'),12)} {pad(r.get('business_fare','-'),12)} {pad(r.get('ac_fare','-'),10)} {pad(r.get('stops','-'),8)}"
            )
        lines.append("-" * 110)
        lines.append("Naye search ke liye 'reset' likhein. Kisi train ki tafseel ke liye number batayein.")
        return "\n".join(lines)


if __name__ == "__main__":
    bot = TrainBookingAI()
    print(bot.process_user_input("karachi jana hai"))
    print(bot.process_user_input("islamabad"))
    print(bot.process_user_input("kal"))
    print(bot.process_user_input("business"))
    print(bot.process_user_input("raat"))
    print(bot.process_user_input("haan"))