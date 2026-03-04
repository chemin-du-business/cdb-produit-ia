from __future__ import annotations
from typing import Any, Dict, List

def _norm(x: float, maxv: float) -> int:
    if maxv <= 0:
        return 0
    v=int(round((x/maxv)*100))
    return max(0,min(100,v))

def score_candidate(c: Dict[str, Any], max_views: int, max_likes: int, max_shares: int) -> Dict[str, Any]:
    sources=c.get("sources",[]) or []
    signals=c.get("signals") or {}

    breakdown={"views":0,"likes":0,"shares":0,"pinterest":0,"multi":0}

    tk=(signals.get("tiktok_hashtag") or {})
    views=int(tk.get("views",0) or 0)
    likes=int(tk.get("likes",0) or 0)
    shares=int(tk.get("shares",0) or 0)

    breakdown["views"]=int(round(_norm(views,max_views)*0.30))   # 0..30
    breakdown["likes"]=int(round(_norm(likes,max_likes)*0.20))   # 0..20
    breakdown["shares"]=int(round(_norm(shares,max_shares)*0.10))# 0..10

    pin=(signals.get("pinterest") or {})
    hits=int(pin.get("hits",0) or 0)
    breakdown["pinterest"]=min(20,hits)

    if "pinterest" in sources:
        breakdown["multi"]=20

    score=sum(breakdown.values())
    score=max(0,min(100,score))
    return {"score":score,"score_breakdown":breakdown}
