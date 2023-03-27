# greenletio change log

**Release 0.10.0** - 2023-03-27

- Optionally preserve contextvars in `async_` decorator [#10](https://github.com/miguelgrinberg/greenletio/issues/10) ([commit](https://github.com/miguelgrinberg/greenletio/commit/620cb485e8485408cf97c7e7cbc8adcb58e34796))
- Functions wrapped with `async_` are now proper coroutines ([commit](https://github.com/miguelgrinberg/greenletio/commit/be7a59a74986ec098302f4762adbe4dbfd2396fc))
- Add python 3.10, 3.11 and pypy 3.8 to builds, remove Python 3.6 ([commit](https://github.com/miguelgrinberg/greenletio/commit/5fad25fb342805340aef9264e0228c914310d244))
- Add a context switching benchmark ([commit](https://github.com/miguelgrinberg/greenletio/commit/66d57e5c89cc6e01951ae8b4c7de6a1e3dde6657))

**Release 0.9.0** - 2021-08-18

- Simplified the `async_` and `await_` functions ([commit](https://github.com/miguelgrinberg/greenletio/commit/0469db503fdc6fe16685830d9ba25d849e8967af))
- Raise a `RuntimeError` when `await_` is used in the asyncio thread ([commit](https://github.com/miguelgrinberg/greenletio/commit/e7c675fbf35d0709d0e9093f1e820f3781394921))
- API reference documentation section ([commit](https://github.com/miguelgrinberg/greenletio/commit/8cd00033da0b52a858d3fe4cf3d5ece3463b6c52))
- Documentation updates ([commit](https://github.com/miguelgrinberg/greenletio/commit/e547fccb018b272f32d308bd4b865cf93d4f09d4))

**Release 0.1.0** - 2021-06-08

- Fixes for Windows ([commit](https://github.com/miguelgrinberg/greenletio/commit/aad9e42f597d9a0c4c05d0267bafeef10c84601a))
- Fix timing errors in unit test ([commit](https://github.com/miguelgrinberg/greenletio/commit/70f669541f5139136723ff98b2d77d8fd9d60648))
- Improved project structure ([commit](https://github.com/miguelgrinberg/greenletio/commit/85877cb37137e83af5ff0bfa8e57f094477766de))
- Documentation ([commit](https://github.com/miguelgrinberg/greenletio/commit/9818c6036689811badfc5d6149f5398306b20565))
- Switch to github actions for builds ([commit](https://github.com/miguelgrinberg/greenletio/commit/d94af9856c7ae1d8fa539e01337e61c8fa690434))

**Release 0.0.7** - 2020-09-12

- Handle pending I/O better in `async_` function ([commit](https://github.com/miguelgrinberg/greenletio/commit/2c1ab23a3a969db6258d52ca52258ad5e4ef45b6))

**Release 0.0.6** - 2020-08-17

- Code cleanup ([commit](https://github.com/miguelgrinberg/greenletio/commit/d46f45ce1aca78aa7bb95590dd9de2f283c9f827))
- Socket benchmark ([commit](https://github.com/miguelgrinberg/greenletio/commit/6a05d076bb69192a3454a41f608240e72f2e3865))
- Performance optimizations for `async_` and `await_` functions ([commit](https://github.com/miguelgrinberg/greenletio/commit/68890209bbf5b8559915acb1ea2441bc8950a256))
- Threading benchmark ([commit](https://github.com/miguelgrinberg/greenletio/commit/cfde239fbea29ea33fde9a78bd9d8954095ab407))

**Release 0.0.5** - 2020-08-03

- Fix setup to include green sub-package ([commit](https://github.com/miguelgrinberg/greenletio/commit/5625f33d557c3fc99f3402261d335de701133435))
- Postgres benchmark scripts ([commit](https://github.com/miguelgrinberg/greenletio/commit/a165464ea4cc6528a3fa04b477cb57ff29a1c5bc))
- Async requests example ([commit](https://github.com/miguelgrinberg/greenletio/commit/90ea05f5456bbc587fe0b7416160bccdd7fb8171))
- Queue can be patched, no need to define it explicitly ([commit](https://github.com/miguelgrinberg/greenletio/commit/003f1f6a56a0e2d203bdf19a31497004814d7866))

**Release 0.0.4** - 2020-08-03

- Nonblocking socket and ssl implementations ([commit](https://github.com/miguelgrinberg/greenletio/commit/b1dde1342514365bfe1b6a282047b77d3e50e601))
- Postgres support via psycopg2 wait callback ([commit](https://github.com/miguelgrinberg/greenletio/commit/9f9e6883061b6486eb91e01cd9334b9a1357f56b))
- Threading and time modules, plus various improvements ([commit](https://github.com/miguelgrinberg/greenletio/commit/18479547ae6641eded556854a9de35e2072997ed))
- I/O waiting support ([commit](https://github.com/miguelgrinberg/greenletio/commit/de8466bf6d5d47cd97ad90ea312cb839f64188e1))
- Queue module ([commit](https://github.com/miguelgrinberg/greenletio/commit/46f6b561b3ea8366415cf4f8bb6e12aca94e38d0))
- Remember loop instance ([commit](https://github.com/miguelgrinberg/greenletio/commit/1e1c3b4f51decfa1220cf7712a9f2594e780f3dc))
- Fixes for pypy3 ([commit](https://github.com/miguelgrinberg/greenletio/commit/f00dc9ca57505288641c6c87576ed95274227f45))
- Threading unit tests ([commit](https://github.com/miguelgrinberg/greenletio/commit/5871207f5554b287acf622f1cb25417d23cf260d))
- Unit testing improvements ([commit](https://github.com/miguelgrinberg/greenletio/commit/8a3de01481143128e79febde5beeddda471bd1b1))
- SSL and patcher unit tests ([commit](https://github.com/miguelgrinberg/greenletio/commit/004e9d29dcafee7946473dd73ddd7a67f9a48c36))
- More socket unit tests ([commit](https://github.com/miguelgrinberg/greenletio/commit/c1fbe4c9ee5698fa7e829637d8e32e6432daceff))
- Unit test reorg ([commit](https://github.com/miguelgrinberg/greenletio/commit/3758f92b9c159f95f5575f8178cbd92ce6b77c83))
- Simple patching support ([commit](https://github.com/miguelgrinberg/greenletio/commit/75cbfafbce2e46c8fe9bba02114bcb43ce8804ce))
- Tox updates ([commit](https://github.com/miguelgrinberg/greenletio/commit/5a28258322376089f72fa00f4f3e39229d58e0d9))

**Release 0.0.3** - 2020-07-19

- Use a faster deque instead of a list ([commit](https://github.com/miguelgrinberg/greenletio/commit/5367590f4750033ce3ffc0d1f9091a97137e8cc8))
- Fix 3.6 unit tests ([commit](https://github.com/miguelgrinberg/greenletio/commit/2e094c4ba7a2708b26ac638793a2df8f2b8dde4d))
- Unit tests ([commit](https://github.com/miguelgrinberg/greenletio/commit/faedac384ef2e3419fbd4cef76ae531d99ef7acd))

**Release 0.0.2** - 2020-07-17

- Improved error handling ([commit](https://github.com/miguelgrinberg/greenletio/commit/22a9e9bbb0f95adec9410aceef07524d3c602996))
- initial version ([commit](https://github.com/miguelgrinberg/greenletio/commit/d0e04759919ae393ebcbebc5025807b14676a724))
- Initial commit ([commit](https://github.com/miguelgrinberg/greenletio/commit/3e371611051ab2f4d3ab406f2714b601ea531d46))
