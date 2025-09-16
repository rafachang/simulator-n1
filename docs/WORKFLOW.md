# 🛠 Git Workflow – Equipment Simulator

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![GitHub last commit](https://img.shields.io/github/last-commit/seu-usuario/seu-repo)
![GitHub repo size](https://img.shields.io/github/repo-size/seu-usuario/seu-repo)

> This guide provides a standardized workflow for contributing to the Equipment Simulator project, ensuring code quality, consistency, and smooth collaboration across multiple machines.

---

## 1️⃣ Setting Up

Before starting development:

1. Open the terminal in the project directory.
2. Ensure you are on the `main` branch and up to date:

git checkout main
git pull origin main

3. Create a new branch for your feature or fix:

git checkout -b feature/your-feature-name
Examples: feature/device-simulation, fix/protocol-bug

---

## 2️⃣ Development Practices

Save changes frequently.

Test your code locally before committing.

Write clear and descriptive commit messages:

feat: add new device simulation
fix: correct protocol parsing
chore: update README or LICENSE

Keep commits atomic: each commit should represent a single logical change.

---

## 3️⃣ Committing Changes

Check the status of your changes:

git status

Stage your changes:

git add .

Commit with a clear message:

git commit -m "brief but descriptive message"

---

## 4️⃣ Syncing with Remote

Always pull before pushing to avoid conflicts:

git pull origin main

Push your feature branch to GitHub:

git push origin feature/your-feature-name

---

## 5️⃣ Merging Changes

After completing a feature or fix:

Open a Pull Request on GitHub targeting main.

Review code and address feedback if needed.

Merge the branch into main.

Delete the feature branch both locally and remotely:

git branch -d feature/your-feature-name        # local
git push origin --delete feature/your-feature-name   # remote

---

## 6️⃣ Project Maintenance

Update requirements.txt whenever new dependencies are added:

pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: update dependencies"
git push origin main


Keep documentation (README.md, WORKFLOW.md, LICENSE) updated.

Organize code in /src and /tests directories for maintainability.

Optionally, configure GitHub Actions for automated testing and CI.

---

## ✅ Best Practices

Follow consistent naming conventions for branches (feature/, fix/, chore/).

Ensure commits are atomic and descriptive.
Test thoroughly before merging to main.

Use code reviews for collaboration, even if working solo.
Maintain a clean and organized repository structure.

Following this workflow ensures your Equipment Simulator project stays professional, maintainable, and easy to collaborate on across multiple machines.