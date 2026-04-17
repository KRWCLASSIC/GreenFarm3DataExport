# Green Farm 3 Data Export (GF3-v4.2.1)

This project contains extracted and decrypted data from the game Green Farm 3 (v4.2.1).

> [!WARNING]
> Scripts were not tested on different versions of the game! I'm not guaranteeing that they will extract data correctly.

## Requirements
To understand the underlying logic or update the scripts for new versions, you may need a JADX export of the game's source code.
- Primary logic used for mapping can be found in `com.gameloft.android.ANMP.GloftGF2F.S800x480.GLLib`.
- Asset structures are highly obfuscated and were reverse-engineered by tracing `GLLib` methods.

## Data Files
- **quest_library.json**: The complete progression map of all 304 quests.
  - `quest_name`: The official title of the quest.
  - `text_box`: Narrative intro dialogue (Cindy Lou, etc.).
  - `description`: The human-readable instruction for the objective.
  - `prerequisite_id`: The internal ID of the quest required to unlock this one.
  - `objectives`: A list of objects containing:
    - `text`: The task description.
    - `count`: The number of items/actions required.
  - `reward_coins` / `reward_xp`: The payout for completing the quest.
- **InitialFeed_decrypted.json**: Decrypted configuration for the game's store and items.

## Scripts
- **extract_quest_library.py**: Parses the game's binary assets (`13` and `EN`) to generate the quest library. Uses a hybrid mapping system to handle various quest layouts (e.g., Tutorials vs Story).
- **decrypt_feed.py**: Decrypts Game Feed binaries (XXTEA) into formatted JSON.
- **dbg_***: Various debugging and research scripts used during the reverse-engineering process. Not public!

## Technical Details
- **Encryption**: Configuration files are decrypted from XXTEA using the hardcoded key `1001`.
- **Quest Resolution**:
  - Quest names are resolved by indexing the localized string pack at `[DialogueID - 1]`.
  - Type-aware logic (Column 12) is used to differentiate between dialogue-heavy and action-heavy quest structures.
  - "Next-Name" filtering is used to prevent subsequent quest titles from leaking into current quest objectives.