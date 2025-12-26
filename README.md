# GenAI Automated Intelligence Pipeline (POC)

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Gemini](https://img.shields.io/badge/AI-Google_Gemini_1.5-orange)
![License](https://img.shields.io/badge/License-MIT-green)

> **Enterprise Scenario Simulation:** A Serverless CI/CD pipeline demonstrating how to leverage Large Language Models (LLM) to automate unstructured data processing and insight delivery.

## 📖 Executive Summary
This project serves as a **Proof of Concept (POC)** for a lightweight, scalable **"AI-Powered Engineering Assistant."**

While the live instance is configured to aggregate and analyze **Global News Data**, the underlying architecture is designed to validate a broader hypothesis: **Generative AI can be reliably integrated into traditional engineering workflows to automate information retrieval and decision support.**

### 🎯 Value Proposition
* **Zero-Cost Infrastructure:** fully operated on **GitHub Actions (Serverless)** without dedicated VM maintenance.
* **Fault Tolerance:** Implements logic to handle API rate limits (429) and model availability checks.
* **Actionable Insights:** Transforms raw noise (web data) into structured intelligence pushed to Instant Messaging platforms (LINE).

---

## 🏗️ Architecture & Engineering Decisions

This solution moves beyond simple scripting by incorporating **DevOps practices** and **Resilient System Design**.

### 🛠 Tech Stack

| Component | Technology | Version / Details |
| :--- | :--- | :--- |
| **Core Runtime** | **Python** | **3.10+** (Optimized for Async I/O) |
| **AI Model** | **Google Gemini** | **1.5 Pro** (Primary) & **1.5 Flash** (Fallback) |
| **SDK** | **Google Generative AI SDK** | `google-generativeai` (Official Python Client) |
| **Orchestration** | **GitHub Actions** | Ubuntu-latest Runner (Serverless Cron Job) |
| **Messaging** | **LINE Messaging API** | RESTful Integration via `requests` |
| **Environment** | **Dotenv** | `python-dotenv` for secure secrets management |

### ⚙️ System Data Flow

```mermaid
graph LR
    subgraph "External World"
    A[Global News Source]
    end

    subgraph "Serverless Pipeline (GitHub Actions)"
    B(Python Script: Fetch & Parse) -->|Raw Text| C{Gemini 1.5 Processing}
    C -->|Fallback Strategy| C1[Model: 1.5 Pro / 1.5 Flash]
    C1 -->|Context-Aware Prompting| D(Structured Insight Generation)
    end

    subgraph "Delivery"
    D -->|JSON Payload| E[LINE Messaging API]
    E -->|Push Notification| F[Decision Maker / Engineer]
    end
