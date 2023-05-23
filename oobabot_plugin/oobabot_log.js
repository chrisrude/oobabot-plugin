var done_all_this = document.getElementById("oobabot_done_all_this");
console.log(done_all_this);
done_all_this.addEventListener(
    "click",
    function () {
        var elem = document.querySelector("#discord_bot_token_accordion > .open");
        elem.click();
    }
);
