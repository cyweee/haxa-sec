const { ethers } = require("ethers");

async function main() {
    // 1. Подключение к сети
    const provider = new ethers.JsonRpcProvider("https://ethereum-sepolia-rpc.publicnode.com");

    // 2. Твой приватный ключ из MetaMask (строка 64 символа)
    const privateKey = "0x3dfd3fe2c49cc53f39aee30152b34e6d3946bd9cda27fb18675ded58bef605aa";
    const wallet = new ethers.Wallet(privateKey, provider);

    const contractAddress = "0x997f3da79A90a6c821F41Dfc31A23B2ce179EF01";

    // 3. Сообщение, которое ТЕБЕ выдал сайт (Step 1)
    const message = "haxagon:316255048"; // ЗАМЕНИ НА СВОЁ

    console.log("Подписываю и отправляю...");

    try {
        const signature = await wallet.signMessage(message);
        const abi = ["function completeTask(string message, bytes signature) public"];
        const contract = new ethers.Contract(contractAddress, abi, wallet);

        const tx = await contract.completeTask(message, signature);
        console.log("Транзакция отправлена! Ждем подтверждения...");
        await tx.wait();
        console.log("Успех! Хэш транзакции:", tx.hash);
        console.log("Теперь иди в Etherscan и ищи Result Hash в логах.");
    } catch (e) {
        console.error("Ошибка:", e.message);
    }
}

main();