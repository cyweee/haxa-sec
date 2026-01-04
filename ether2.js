const { ethers } = require("ethers");

async function signChallenge() {
    const privateKey = "0x3dfd3fe2c49cc53f39aee30152b34e6d3946bd9cda27fb18675ded58bef605aa";
    const wallet = new ethers.Wallet(privateKey);

    // ВСТАВЬ СЮДА СТРОКУ ИЗ ШАГА 3 НА САЙТЕ
    const challenge = "3p02ul3ep9x19duy";

    const signature = await wallet.signMessage(challenge);
    console.log("Твоя финальная подпись:");
    console.log(signature);
}

signChallenge();