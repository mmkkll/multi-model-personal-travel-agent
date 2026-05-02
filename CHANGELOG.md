# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.0.1] — 2026-05-01

### Changed
- **Booking detection whitelist extended** in `travel-organizer/organizer-prompt.md` — Gmail search query now matches more car-rental brands and Italian receipt subjects. Added to subject keywords: `voucher`, `autonoleggio`. Added to from-list: `drivalia`, `budget`, `alamo`, `enterprise`, `thrifty`, `dollar` (joining the existing `hertz`, `europcar`, `avis`, `centauro`, `goldcar`, `firefly`, `sixt`).

### Reasoning
- Real-world miss: a Centauro "Voucher di conferma della prenotazione …" email did not match the prior subject filter because the keyword `voucher` was missing. Whitelist hardened based on observed misses.
- The Italian word "autonoleggio" (car rental) is common in Italian booking flows and was missing.
- Drivalia (Italian car rental brand, ex Goldcar/Locauto group) and the Big-5 US chains (Budget, Alamo, Enterprise, Thrifty, Dollar) are common enough on international trips to warrant inclusion.

## [1.0.0] — 2026-04-29

### Added
- Initial release: Multi-Model Personal Travel Agent.
- Self-hosted travel research that combines Gemini, Perplexity, OpenAI, Duffel multi-origin flight search, and Google Maps Routes (transit) — all in parallel, in a single n8n workflow.
- Telegram bot interface (long-polling, no webhook → no 60s response constraint).
- Travel Document Organizer: cron prompt that scans Gmail for booking confirmations and speaker invitations, classifies trips work vs leisure, files them into a Notion workspace (Inspirations → Planning → Business/Work → Past trips).
- MIT licensed.
