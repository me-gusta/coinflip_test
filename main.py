import random
from decimal import Decimal
from typing import Optional, Union, List

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from pure import to_decimal, calc_multiplier


class MultiplyGame(BaseModel):
    flips_count: int = 0
    history: List[str] = list()
    bet: Decimal


class MockState(BaseModel):
    balance: Decimal
    game: Optional[MultiplyGame]


middleware = [
    Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
]

app = FastAPI(middleware=middleware)

state = MockState(
    balance=to_decimal(1000)
)


@app.middleware("http")
async def process_auth(request: Request, call_next):
    check_string = request.headers.get('X-CHECK-STRING')
    # if not check_string:
    #     return JSONResponse(status_code=400, content={'detail': 'No X-CHECK-STRING provided'})
    return await call_next(request)


@app.post("/getUser")
async def get_user():
    if state.game:
        game = {
            "history": state.game.history,
            "bet": state.game.bet,
            "multiplier": calc_multiplier(state.game.flips_count),
            "next_multiplier": calc_multiplier(state.game.flips_count + 1)
        }
    else:
        game = None
    return {
        "game": game,
        "balance": state.balance,
        "language_code": "ru",
        "preferences": {
            "last_bet": to_decimal("1"),
            "last_type": random.choice(['instant', 'multiply'])
        }}


# =====================

class InstantPlay(BaseModel):
    bet: Decimal
    prediction: str
    win: Optional[bool]


@app.post("/instant/play")
async def instant_play(params: InstantPlay):
    if state.game and params.bet:
        raise HTTPException(status_code=400, detail=f'A running game found. bets cannot be accepted.')

    multiplier = Decimal("0.94")
    bet = to_decimal(params.bet)

    if params.win is not None:
        result = params.win
    else:
        result = random.choice(['HEADS', 'TAILS']) == params.prediction

    if result:
        state.balance += to_decimal(bet * multiplier)
        return {'victory': True, 'balance': state.balance}
    else:
        state.balance -= bet
        return {'victory': False, 'balance': state.balance}


# =====================

class MultiplyPlay(BaseModel):
    bet: Optional[Decimal]
    prediction: str
    win: Optional[bool]


@app.post('/multiply/play')
async def multiply_play(params: MultiplyPlay):
    if not state.game:
        if not params.bet:
            raise HTTPException(status_code=400, detail=f'No bet specified')
        state.game = MultiplyGame(bet=to_decimal(params.bet))
    elif params.bet:
        raise HTTPException(status_code=400, detail=f'A running game found. bets cannot be accepted.')

    if params.win is not None:
        result = params.win
    else:
        result = random.choice(['HEADS', 'TAILS']) == params.prediction

    if result:
        state.game.history.append(params.prediction)
        state.game.flips_count += 1
        return {'victory': True,
                "multiplier_next": calc_multiplier(state.game.flips_count + 1),
                "multiplier": calc_multiplier(state.game.flips_count)}
    else:
        state.balance -= state.game.bet
        state.game = None
        return {'victory': False,
                'balance': state.balance}


@app.post("/multiply/cashout")
async def multiply_cashout():
    if not state.game:
        raise HTTPException(status_code=400, detail=f'No game running')

    multiplier = calc_multiplier(state.game.flips_count)
    state.balance += to_decimal(state.game.bet * multiplier)
    state.game = None
    return {'balance': state.balance}
