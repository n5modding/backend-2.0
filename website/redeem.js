const redeemBtn = document.getElementById("redeemBtn");
const codeInput = document.getElementById("codeInput");
const message = document.getElementById("message");

redeemBtn.addEventListener("click", async () => {
    const code = codeInput.value.trim();
    if (!code) {
        message.textContent = "Please enter a code.";
        return;
    }

    try {
        const res = await fetch("/backend/redeem", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code })
        });
        const data = await res.json();
        message.textContent = data.message;
        if (data.status === "success") {
            document.cookie = `redeemedCode=${code}; max-age=${2*24*60*60}; path=/`;
        }
    } catch (err) {
        message.textContent = "Error redeeming code.";
        console.error(err);
    }
});
