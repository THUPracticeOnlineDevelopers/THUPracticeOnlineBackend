# THUPracticeOnlineBackend
This is the offical repo for the backend of THUPracticeOnline.

## What is THUPracticeOnline?
**THUPracticeOnline**, also **酒井实践在线** in Chinese, is an open-source project completed in **Software Engineering 2025 Spring**. It is aimed at providing all the essential service used in the workflow of THU's practice. In our team, [misharo9](https://github.com/misharo9) and [zzzzuzzzz](https://github.com/zzzzuzzzz)  are responsible for the backend. And [InitiatorAtao](https://github.com/InitiatorAtao) and [zou-git](https://github.com/zou-git) are responsible for the frontend.

## How to get started?
THUPracticeOnline is deployed in **Gitlab**, using Gitlab's **CI/CD**. You should upload this repo in Gitlab and run the CI/CD process.

In `THUPracticeOnline_backend/settings.py`, we deleted the information of `secret key`, the user id and the password of `database`, `offical email` and `feishu`. Also in `start.sh` and `dev-start.sh`, we deleted the id and password of backend administrator. You should first fill these up with your own account.

If you want run this project locally, you should change the database in `THUPracticeOnline_backend/settings.py` into a local database, like `sqlite`. Then run
```bash
pip install -r requirements.txt
bash start.sh
```