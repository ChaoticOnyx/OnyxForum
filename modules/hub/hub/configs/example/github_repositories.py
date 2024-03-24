import typing
from hub.github.repository import *

repositories: typing.Dict[str, Repository] = {
    "onyxbay": Repository(
        name = "ChaoticOnyx/OnyxBay",
        labels = Labels(
            bug = Label(name = "🐞 баг"),
            feature = Label(name = "🔩 улучшение"),
            sprite = Label(name = "🎨 спрайты"),
            owners_approved = Label(name = "🔵 одобрено"),
            verification_required = Label(name = "🔵 требуется проверка"),
            design_elaboration_required = Label(name = ":red_circle: требуется проработка"),
            design = Label(name = "🌌геймдизайн"),
            bounty = Label(name = "💰 награда"),
            ideas_required = Label(name = "💡 нужны идеи"),
            robot = Label(name = ":robot:создано роботом"),
            postponed = Label(name = "🕗 отложено"),
            waiting_author = Label(name = ":white_circle: ожидает автора"),
            wiki = Label(name = "🌐 вики"),

            difficulty_unreal = Label(name = ":goberserk: сложнее тех двух"),
            difficulty_very_hard = Label(name = ":rage1: очень сложно"),
            difficulty_hard = Label(name = ":suspect: сложно"),
            difficulty_easy = Label(name = ":godmode: просто"),
            
            priority_max = Label(name = "🔥 приоритет"),
            priority_high = Label(name = "🔺 приоритет"),
            priority_low = Label(name = "🔻 приоритет"),
        ),
        discord_guilds = [
            DiscordGuild(
                id = 414832443384659968,
                channels = DiscordChannels(
                    heads = 464188191423987712,
                    developers = 686884175822716953,
                    owners = 697914765304922132,
                    designers = 697914765304922132,
                    watchers = 414840922652803073,
                    spriters = 414840922652803073,
                    beginners = 414840922652803073,
                    webhook = 423205687133470721,
                )
            )
        ]
    )
}
