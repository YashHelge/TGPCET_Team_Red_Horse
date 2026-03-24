The Indian financial landscape has undergone a seismic shift over the last decade, transitioning from a traditional preference for physical assets like gold and real estate toward digital financial instruments. This evolution has been catalyzed by the emergence of low-cost brokerage platforms, the proliferation of high-speed internet, and a favorable regulatory environment. However, this democratization of market access has brought with it a surge in retail participation that is often susceptible to psychological vulnerabilities. The phenomenon of "SheepOrSleep," where investors either follow the herd in a panic or remain dormant through critical market shifts, represents a significant challenge to individual wealth accumulation and overall market stability. The development of an AI-driven behavioral bias detector provides a sophisticated technological solution to identify, quantify, and mitigate these irrational decision-making patterns in real-time.

## **The Behavioral Landscape of Indian Retail Investing**

The psychological profile of the modern Indian investor is a complex interplay of cognitive psychology, market information availability, and socio-economic factors.1 Research indicates that investor cognitive psychology, market information, and stock characteristics are the top-ranked factors driving herding behavior in the Indian context, while socio-economic factors, though present, play a comparatively smaller role.1 This suggests that the primary triggers for irrational behavior are rooted in how information is processed rather than the external economic environment alone.

In the Indian stock market, herd behavior—where investors imitate the actions of others rather than evaluating information independently—is notably pronounced during down-market conditions.2 This behavior is not uniform across the market; sector-specific analysis reveals strong evidence of herding in the capital goods and IT sectors, whereas the banking sector often displays a higher propensity for independent decision-making.2 This discrepancy is often attributed to the levels of institutional ownership and the depth of analyst coverage in different sectors.

| Bias Component | Impact on Decision-Making | Observed Market Outcome |
| :---- | :---- | :---- |
| Loss Aversion | Investors feel the pain of losses more acutely than the joy of gains. | Holding losing positions too long in hopes of a rebound (the disposition effect). 4 |
| Hyperbolic Discounting | Prioritizing immediate emotional relief over long-term rational profit. | Panic selling during temporary market volatility to stop "perceived" pain. 6 |
| Representativeness Bias | Assuming that a short-term trend is representative of a permanent shift. | Chasing recent high-performing sectors (e.g., Pharma in 2020\) at their peaks. 4 |
| Herd Mentality | Suppressing private information to follow the crowd's direction. | Mass entry into speculative IPOs or "meme stocks" driven by social media. 1 |

The presence of herding behavior leads to stock market deviations from fundamental values, creating speculative bubbles and subsequent crashes.1 For example, during the March 2020 COVID-19 crash, the Indian market witnessed a rapid 23% decline, a phenomenon inadequately explained by traditional finance but clearly illustrated by behavioral biases such as availability bias and regret aversion operating simultaneously.4

## **Econometric Detection of Herd Behavior and Panic Selling**

To programmatically detect irrational market regimes, the bias detector utilizes non-linear econometric models that analyze the dispersion of stock returns. The two primary methodologies employed are the Cross-Sectional Standard Deviation (CSSD) and the more robust Cross-Sectional Absolute Deviation (CSAD).

## **The Chang, Cheng, and Khorana (CCK) Model**

The CCK model is built on the premise that rational asset pricing models predict a linear relationship between the dispersion of individual stock returns and market returns. When herding occurs, this relationship becomes non-linear. In periods of extreme market movement, the return dispersion increases at a decreasing rate—or even decreases—as investors ignore their idiosyncratic information to follow the market trend.10

The mathematical formulation for the CSAD is defined as:

![][image1]  
Where ![][image2] is the return of an individual stock and ![][image3] is the cross-sectional average return of the market. To test for herding, a quadratic regression is performed:

![][image4]  
In this model, if ![][image5] is statistically significant and negative, it provides empirical evidence of herding behavior.2 This occurs because during large market swings, the individual returns of stocks "cluster" around the market return more closely than predicted by linear models.

## **Identifying Panic-Selling Regimes**

Panic selling, or "freak-outs," can be identified through a specific heuristic: a decline of 90% in a household account's equity assets over the course of one month, where 50% or more of that decline is due to active trades rather than price depreciation.13 Machine learning models can predict these events with significant accuracy by integrating investor demographics, portfolio history, and current market conditions. Studies show that males over the age of 45 with more dependents are statistically more likely to engage in such freak-out behavior.6

| Metric | Rational Market Expectation | Herding/Panic Indicator |
| :---- | :---- | :---- |
| CSAD/Market Return | Linear, positive correlation. | Non-linear, negative quadratic term (![][image5]). 2 |
| Trading Volume | Correlated with information flow. | Asymmetric spikes during down-markets without news. 12 |
| Delivery Percentage | High delivery indicates long-term conviction. | Low delivery during price drops suggests speculative panic. 14 |

## **Self-Dependent Data Acquisition and Stealth Scraping Strategies**

Building a real-time bias detector for the Indian market requires a continuous stream of data from the National Stock Exchange (NSE) and Bombay Stock Exchange (BSE) without relying on expensive, key-based APIs.

## **Free and Open-Source Data Libraries**

The system utilizes specialized open-source libraries that are designed to bypass the 403 Forbidden errors typically encountered on Indian exchange sites:

* **PNSEA (Python NSE API):** A powerful, stealthy library that uses stealthkit to rotate TLS fingerprints and headers, making requests look like a human browsing on Chrome or Safari.16 It fetches quotes, historical prices, and even mutual fund movements without triggering rate-limit blocks.  
* **bsedata / bse:** These libraries provide unofficial API access to real-time quotes and corporate announcements directly from the Bombay Stock Exchange.18  
* **Indian-Stock-Market-API:** A free REST API that fetches real-time data for both exchanges via Yahoo Finance without requiring any API key or authentication.20

## **Advanced Anti-Bot Evasion for Financial Portals**

For scraping information from portals like Moneycontrol or AMFI, the system employs modern, undetectable browser automation tools:

1. **Nodriver / XDriver:** These are next-generation automation frameworks that bypass modern anti-bot systems like Cloudflare WAF and Turnstile. Unlike standard Selenium, they patch Playwright at the source level to remove automation signatures like navigator.webdriver.  
2. **TLS Fingerprinting (JA3):** The system uses curl\_cffi to mimic the TLS handshake of specific browser versions, preventing detection at the network layer.21  
3. **Human Mimicry Module:** Scrapers simulate erratic mouse movements, variable scroll speeds, and randomized dwell times between requests to lower their "bot score".22

| Scraping Tool | Evasion Mechanism | Use Case |
| :---- | :---- | :---- |
| PNSEA | TLS/Header Rotation | Real-time NSE stock prices and option chains. 17 |
| bsedata | BeautifulSoup/Request | Real-time BSE quotes and list of gainers/losers. 19 |
| Nodriver | CDP Leak Prevention | Scraping news headlines and sentiment from protected sites. |

## **Self-Hosted AI Frameworks for Local Sentiment Analysis**

To remain independent of paid LLM APIs (like GPT-4), the system uses locally hosted open-source models for sentiment analysis and pattern recognition.

## **Local LLM Hosting with Ollama**

The architecture integrates **Ollama**, an open-source platform that allows running Large Language Models (like **Llama 3 8B**) on standard hardware with GPU acceleration.

* **Zero-Cost Inference:** By hosting Llama 3 locally, the system performs deep news analysis and behavioral categorization for thousands of stocks without recurring subscription fees.  
* **Financial Sentiment with FinBERT:** The system also utilizes **FinBERT**, a BERT-based model specifically fine-tuned for financial nomenclature.24 It processes news titles to compute a Daily Sentiment Score (![][image6]), which is then fed into the herding detection engine.24

## **Telegram and Social Scraping**

Real-time sentiment is enriched by scraping free SEBI-registered Telegram channels (e.g., Equitymaster, Nifty Stock Trades) that share market analysis and community engagement signals. This allows the system to correlate "social noise" with actual investor flows.

## **Scalable Open-Source Data Pipeline Architecture**

To process data for 6,000+ Indian stocks in real-time, the system requires a high-throughput, self-hosted infrastructure.

## **The Streaming Core: Apache Kafka and PyFlink**

The architecture uses **Apache Kafka** as a distributed message broker to decouple ingestion (scrapers) from processing (ML models).27 This ensures durability; if a sentiment analyzer service crashes, Kafka buffers the events so they can be replayed once the service is restored.29 Real-time windowed aggregations (like VWAP or RSI) are handled by **PyFlink**, providing HFT-grade analytics on a developer-friendly stack.30

## **Analytical Storage: ClickHouse and DuckDB**

* **ClickHouse:** A columnar OLAP database that can ingest data directly from Kafka and perform sub-second analytical queries on billions of rows.30 It is ideal for calculating the CSAD across the entire BSE 500 index.30  
* **DuckDB:** Used for local, embedded analytics within the dashboard for immediate portfolio comparison without the overhead of a full server.34

| Stage | Free Technology | Function |
| :---- | :---- | :---- |
| Ingestion | PNSEA / Nodriver | Stealth scraping of NSE/BSE and news sites. |
| Message Broker | Apache Kafka | Event buffering and stream distribution. 27 |
| Processing | Polars / PyFlink | Fast vectorized data manipulation and metrics. 34 |
| AI Inference | Ollama / FinBERT | Self-hosted sentiment and behavioral analysis. |
| Storage | ClickHouse | Columnar storage for long-term historical analysis. 30 |
| Visualization | Streamlit / Plotly | Interactive dashboards for behavior gap analysis. |

## **Personalized Nudge Engine and Behavioral Intervention**

The "SheepOrSleep" solution moves beyond detection to influence investor behavior using an agentic AI nudge system powered by local models.

## **Agentic Financial Co-Pilot**

Modern apps are pivoting from static tools to "financial co-pilots". Using the local Llama 3 model, the system analyzes a user's portfolio in context of market volatility and triggers real-time alerts:

* **Goal Anchoring:** If a user attempts to sell during a dip, the system reframes the action: "This sale will delay your 'Child's Education' goal by 14 months. Are you sure you want to exit during this temporary correction?"35  
* **SIP Discipline:** Using Rupee-Cost Averaging insights, the system shows that staying invested during a 10% dip actually lowers the average acquisition cost, accumulating more units for long-term growth.5  
* **Panic Alerts:** If herding levels in a specific ticker are high, the system warns: "This stock is currently driven by social media hype. Historical data shows such surges are followed by a 15% correction. Review the fundamentals before buying."

## **Comparative Benchmarking of the "Behavior Gap"**

A core feature is the visual demonstration of the financial cost of irrationality. The **Behavior Gap** is the difference between an investment's organic return and what an investor actually earns due to poor timing.7

## **Portfolio Simulation logic**

The system runs local Monte Carlo simulations to compare two profiles:

1. **Disciplined Investor:** Consistently follows a Systematic Investment Plan (SIP) regardless of market conditions.7  
2. **Panic Seller:** Exits the market after a 10% drop and remains in cash for 90 days before re-entering.13

Visualizations in **Streamlit** highlight that missing just 10 of the best-performing days in a 20-year cycle can reduce long-term returns by over 50%.5 This evidence-based approach anchors the user's decision-making in data rather than emotion.40

## **Scalability and Future Outlook**

The entire SheepOrSleep stack is designed to be containerized using **Docker**, allowing it to scale horizontally from a single developer machine to a multi-node cluster as data volume grows.32 By using open-source libraries like pnsea and self-hosted databases like ClickHouse, the system eliminates all recurring vendor costs while providing professional-grade performance for all types of Indian stocks.17

This architecture solves the actual problem of retail panic by providing a transparent, data-driven "mirror" that reflects an investor's patterns, guiding them away from fear and toward intentional, long-term wealth creation.35

#### **Works cited**

1. What make investors herd while investing in the Indian stock market? A hybrid approach | Review of Behavioral Finance | Emerald Publishing, accessed March 24, 2026, [https://www.emerald.com/rbf/article-split/15/1/19/364859/What-make-investors-herd-while-investing-in-the](https://www.emerald.com/rbf/article-split/15/1/19/364859/What-make-investors-herd-while-investing-in-the)  
2. Traces of Herd Behaviour over a decade in Indian Stock Markets \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/379881765\_Traces\_of\_Herd\_Behaviour\_over\_a\_decade\_in\_Indian\_Stock\_Markets](https://www.researchgate.net/publication/379881765_Traces_of_Herd_Behaviour_over_a_decade_in_Indian_Stock_Markets)  
3. Traces of Herd Behaviour Over a Decade in Indian Stock Markets, accessed March 24, 2026, [https://mjmrp.mdim.ac.in/doi/pdf/10.1177/mjmrp.241290586.pdf](https://mjmrp.mdim.ac.in/doi/pdf/10.1177/mjmrp.241290586.pdf)  
4. Understanding the Psychology of March 2020 Stock Market Crash \- Banaras Hindu University, accessed March 24, 2026, [https://www.bhu.ac.in/Images/files/BMReview-Vol\_8-P58-62.pdf](https://www.bhu.ac.in/Images/files/BMReview-Vol_8-P58-62.pdf)  
5. The Behavioural Gap: Why Investors Earn Less Than Their Investments | AssetPlus, accessed March 24, 2026, [https://www.partners.assetplus.in/post/the-behavioural-gap-investors-returns](https://www.partners.assetplus.in/post/the-behavioural-gap-investors-returns)  
6. Unraveling Investor Behavior: The Role of Hyperbolic Discounting in Panic Selling Behavior on the Global COVID-19 Financial Crisis \- PMC, accessed March 24, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC11428550/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11428550/)  
7. The gap between investor return and investment return | Articles | Morningstar India, accessed March 24, 2026, [https://www.morningstar.in/posts/68952/the-gap-between-investor-return-and-investment-return.aspx](https://www.morningstar.in/posts/68952/the-gap-between-investor-return-and-investment-return.aspx)  
8. Behavioral finance in reatail investing \- an Indian perspective \- IOSR Journal, accessed March 24, 2026, [https://iosrjournals.org/iosr-jbm/papers/Vol27-issue10/Ser-7/I2710078193.pdf](https://iosrjournals.org/iosr-jbm/papers/Vol27-issue10/Ser-7/I2710078193.pdf)  
9. View of Herding Behavior in the Indian Stock Market : An Empirical Study, accessed March 24, 2026, [https://indianjournalofcomputerscience.com/index.php/IJF/article/view/164495/113478](https://indianjournalofcomputerscience.com/index.php/IJF/article/view/164495/113478)  
10. What Explains Herd Behavior in the Chinese Stock Market \- Institute of Global Economics and Finance, accessed March 24, 2026, [https://www.igef.cuhk.edu.hk/paper/what-explains-herd-behavior-in-the-chinese-stock-market/](https://www.igef.cuhk.edu.hk/paper/what-explains-herd-behavior-in-the-chinese-stock-market/)  
11. The Impact of Herd Behavior on the Chinese Stock Market \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/358585679\_The\_Impact\_of\_Herd\_Behavior\_on\_the\_Chinese\_Stock\_Market](https://www.researchgate.net/publication/358585679_The_Impact_of_Herd_Behavior_on_the_Chinese_Stock_Market)  
12. Asymmetric Effect of Investors Sentiments on Herding Behavior and Stock Returns: Pre and Post Covid-19 Analysis, accessed March 24, 2026, [http://www.mnje.com/sites/mnje.com/files/v19n1/043-055%20-%20Bagh%2C%20Khan%2C%20Fenyves%2C%20Olah.pdf](http://www.mnje.com/sites/mnje.com/files/v19n1/043-055%20-%20Bagh%2C%20Khan%2C%20Fenyves%2C%20Olah.pdf)  
13. When Do Investors Freak Out? Machine Learning Predictions of Panic Selling \- DSpace@MIT, accessed March 24, 2026, [https://dspace.mit.edu/bitstream/handle/1721.1/141712/2022\_Freakout\_JFDS.pdf?sequence=5\&isAllowed=y](https://dspace.mit.edu/bitstream/handle/1721.1/141712/2022_Freakout_JFDS.pdf?sequence=5&isAllowed=y)  
14. Delivery Volume in the Cash Market: A Key Indicator for Investors \- Tradejini, accessed March 24, 2026, [https://www.tradejini.com/blogs/delivery-volume-in-the-cash-market-a-key-indicator-for-investors](https://www.tradejini.com/blogs/delivery-volume-in-the-cash-market-a-key-indicator-for-investors)  
15. Why Trading Volume and Delivery Scans for Intraday Trading, accessed March 24, 2026, [https://intradayscreener.com/blog/trading-volume-delivery-percentage-in-intraday-trading](https://intradayscreener.com/blog/trading-volume-delivery-percentage-in-intraday-trading)  
16. My 4th pypi lib: I created a stealthy NSE India API scrapper (Python) : r/webscraping \- Reddit, accessed March 24, 2026, [https://www.reddit.com/r/webscraping/comments/1q4ie6b/my\_4th\_pypi\_lib\_i\_created\_a\_stealthy\_nse\_india/](https://www.reddit.com/r/webscraping/comments/1q4ie6b/my_4th_pypi_lib_i_created_a_stealthy_nse_india/)  
17. pnsea · PyPI, accessed March 24, 2026, [https://pypi.org/project/pnsea/](https://pypi.org/project/pnsea/)  
18. bse \- PyPI, accessed March 24, 2026, [https://pypi.org/project/bse/](https://pypi.org/project/bse/)  
19. bsedata \- PyPI, accessed March 24, 2026, [https://pypi.org/project/bsedata/](https://pypi.org/project/bsedata/)  
20. Indian Stock Market API \- NSE & BSE Real-Time Data \- GitHub, accessed March 24, 2026, [https://github.com/0xramm/Indian-Stock-Market-API](https://github.com/0xramm/Indian-Stock-Market-API)  
21. How to Bypass Cloudflare When Web Scraping in 2026 \- Scrapfly Blog, accessed March 24, 2026, [https://scrapfly.io/blog/posts/how-to-bypass-cloudflare-anti-scraping](https://scrapfly.io/blog/posts/how-to-bypass-cloudflare-anti-scraping)  
22. Modern Web Scraping: How to Actually Bypass Anti-Bot Systems \- SitePoint, accessed March 24, 2026, [https://www.sitepoint.com/modern-web-scraping/](https://www.sitepoint.com/modern-web-scraping/)  
23. How to Bypass Cloudflare with Playwright in 2026 \- BrowserStack, accessed March 24, 2026, [https://www.browserstack.com/guide/playwright-cloudflare](https://www.browserstack.com/guide/playwright-cloudflare)  
24. Real-Time Stock News Sentiment Analyzer | by Raviraj Shinde \- Towards AI, accessed March 24, 2026, [https://pub.towardsai.net/real-time-stock-news-sentiment-analyzer-54eaa91c5634](https://pub.towardsai.net/real-time-stock-news-sentiment-analyzer-54eaa91c5634)  
25. FinBERT \- QuantConnect.com, accessed March 24, 2026, [https://www.quantconnect.com/docs/v2/writing-algorithms/machine-learning/hugging-face/popular-models/finbert](https://www.quantconnect.com/docs/v2/writing-algorithms/machine-learning/hugging-face/popular-models/finbert)  
26. Financial Sentiment Analysis Using FinBERT with Application in Predicting Stock Movement, accessed March 24, 2026, [https://arxiv.org/html/2306.02136v3](https://arxiv.org/html/2306.02136v3)  
27. real-time-data-pipelines-python-kafka-stream-processing | Medium, accessed March 24, 2026, [https://medium.com/@currun95/mastering-real-time-data-pipelines-in-python-445340221680](https://medium.com/@currun95/mastering-real-time-data-pipelines-in-python-445340221680)  
28. Building a Modern Data Pipeline Architecture with Python, Kafka, Airflow, Teradata & Tableau | by Mahabir Mohapatra | Medium, accessed March 24, 2026, [https://mhmohapatra.medium.com/building-a-modern-data-pipeline-architecture-with-python-kafka-airflow-teradata-tableau-e8b02ef69648](https://mhmohapatra.medium.com/building-a-modern-data-pipeline-architecture-with-python-kafka-airflow-teradata-tableau-e8b02ef69648)  
29. Building My Own Real-Time Data Pipeline with Python: From Raw Logs to Clean Dashboards, accessed March 24, 2026, [https://python.plainenglish.io/building-my-own-real-time-data-pipeline-with-python-from-raw-logs-to-clean-dashboards-bb12e1f5932d](https://python.plainenglish.io/building-my-own-real-time-data-pipeline-with-python-from-raw-logs-to-clean-dashboards-bb12e1f5932d)  
30. Building a Real Time HFT-Grade Analytics Pipeline with Kafka, PyFlink & ClickHouse, accessed March 24, 2026, [https://medium.com/@sumit160493/building-a-real-time-hft-grade-analytics-pipeline-with-kafka-pyflink-clickhouse-e206383f18b7](https://medium.com/@sumit160493/building-a-real-time-hft-grade-analytics-pipeline-with-kafka-pyflink-clickhouse-e206383f18b7)  
31. GitHub \- MarkPhamm/local\_streaming\_pipeline: End-to-end real-time analytics pipeline with Kafka, Spark micro-batch/Spark Streaming/Flink, ClickHouse, and live dashboards., accessed March 24, 2026, [https://github.com/MarkPhamm/local\_streaming\_pipeline](https://github.com/MarkPhamm/local_streaming_pipeline)  
32. Kafka ClickHouse: Real-Time Data Pipeline for Beginners \- DEV Community, accessed March 24, 2026, [https://dev.to/mohhddhassan/kafka-clickhouse-real-time-data-pipeline-for-beginners-m1p](https://dev.to/mohhddhassan/kafka-clickhouse-real-time-data-pipeline-for-beginners-m1p)  
33. Building a Robust Data Pipeline with Kafka and ClickHouse | The Write Ahead Log, accessed March 24, 2026, [https://platformatory.io/blog/Building-a-Robust-Data-Pipeline-with-Kafka-and-ClickHouse/](https://platformatory.io/blog/Building-a-Robust-Data-Pipeline-with-Kafka-and-ClickHouse/)  
34. How to Build a Real-Time Streaming Data Pipeline on Your Laptop \- Virendra Pratap Singh, accessed March 24, 2026, [https://vpsn-99.medium.com/how-to-build-a-real-time-streaming-data-pipeline-on-your-laptop-1ce941c31db7](https://vpsn-99.medium.com/how-to-build-a-real-time-streaming-data-pipeline-on-your-laptop-1ce941c31db7)  
35. How Investment Insights Reduce Panic Selling \- BillCut, accessed March 24, 2026, [https://www.billcut.com/blogs/investment-insights-panic-selling/](https://www.billcut.com/blogs/investment-insights-panic-selling/)  
36. Case Study : Product Strategy for Groww | by Bhavya Batra \- Medium, accessed March 24, 2026, [https://medium.com/@buildwithbhavya/case-study-product-strategy-for-groww-ce871febf3c3](https://medium.com/@buildwithbhavya/case-study-product-strategy-for-groww-ce871febf3c3)  
37. What is the Behaviour Gap and How Can Investors Close it?, accessed March 24, 2026, [https://behaviouralinvestment.com/2025/06/03/what-is-the-behaviour-gap-and-how-can-investors-close-it/](https://behaviouralinvestment.com/2025/06/03/what-is-the-behaviour-gap-and-how-can-investors-close-it/)  
38. Investing for the Future: A Python Code for Calculating Investment Returns with Dollar-Cost Averaging | by Gradient Drift | Medium, accessed March 24, 2026, [https://yanwei-liu.medium.com/investing-for-the-future-a-python-code-for-calculating-investment-returns-with-dollar-cost-15f7f4a1bb1f](https://yanwei-liu.medium.com/investing-for-the-future-a-python-code-for-calculating-investment-returns-with-dollar-cost-15f7f4a1bb1f)  
39. Scenario Analysis in Python: Advanced Investment Risk Analysis | by Michael Whittle | Coinmonks | Medium, accessed March 24, 2026, [https://medium.com/coinmonks/scenario-analysis-in-python-advanced-investment-risk-analysis-d7d550237295](https://medium.com/coinmonks/scenario-analysis-in-python-advanced-investment-risk-analysis-d7d550237295)  
40. What Is The Behavior Gap? \- 310 Wealth Planning, accessed March 24, 2026, [https://310wealth.com/what\_is\_the\_behavior\_gap/](https://310wealth.com/what_is_the_behavior_gap/)  
41. What is a 'behavior gap'? \- Sugarloaf Wealth Management, accessed March 24, 2026, [https://www.swmllc.com/what-is-a-behavior-gap/](https://www.swmllc.com/what-is-a-behavior-gap/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAA4CAYAAABAFaTtAAAFfUlEQVR4Xu3dWchtUxwA8GWe55lImYeI8CT3dJMx8UA3Q5QMkcyZ4tWYMXLpJjLmwfxgiKtQhAjhRUQUHgzFDYn1b+/trLu+8917zv3u+b6D36/+nbX+6/Sd8+39cP6tvdfaKQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMBE2yfHXznuavtLcvzRHwYAYBJsluOrtn1vOQAAwNxbtX3dPsfeORYUYwAATID9ivYdObYu+gAArAS9HIvq5AhuKNqfFG0AAFaiZ+sEAACTRcEGADDhFGwAABNOwQYAMOGGLdhig9wVCQAAZmjYgm3/HL+n4YuwnXPcn+PaKg8AwIheyrFenZzGpakp2EbZb+3bOpGtUSf+gzatEwAAs+W71BRtl9QD01izTqRm/7f/umvqBAAwHvGMzC9ybNL2j8zx5z+jKT2RY9u2fVKOm4qx0jNp8KXEvdLU/C+pef8k6+5PG3ZmrtarE61y8904ticU/XE7J8cpbXuVHL/mWK0/PDIFGwDMgtNzPJhj7Sr/U9H+vGiHY6t+p7uUWDsrTc3H0wPq3KR5LzXf8YF6YEi9OpHtnuO6oh/H/6GiP25xrjcq+p/l2KPoj0rBBgBj9nqavmgqZ33iJvx48PmynJHjwDT47/2Q47UqF7N4g95bOj71Z7kGxfr9t45NXBKNz4rFBaPq1Yns6dR/mHzcI1fOZI7bQal/zOP+ul6OT/8ZXTEKNgAYs/jxvqBODrBDjltSc+n0/WosdJdL102Di7DIza9yL7b5sFOOQ4uxSbMkNd/1xnpgOXpVP/7H7n+OGc2XU3NZsnNR0e7Ux20mFqfmHIajc3xTjA2ru5zaUbABwJhF8XBwnUzNZbsQM0FRrHU2TIMLsufT0jNftZ9zrFXlYtbuy7Z9Z46rirGZKr/L8mIYp6XmveVl4mH0qv71aenPjK1AYtarc0DR7nxQJ1rnpmbl66CYThzz7vJrFIzD/v+lONclBRsAjFn8YN9a5WImrVsZeXuOm4uxWAl5f9EPcU9U6Y0c2xX9U3NcVvRDXG69sG0vSM0M1rIKjbm2cY7z6uQQelU/jvfjbXv1HL+l/v1jG+R4pW13olj7OvUL6JmKz9+3bV/d9jvH5bg8NYVz7FkX5+fiYjy+Q5yjuIxeUrABwCzopebm+lixWV+Sey7HFqkp0l7NcWUxFjM0sdLz+9RsNhviBz1WHX7c9hempiiIIq77sb8ix1bteGeSf/RjBeVTdXJIvaL9UWqOxYdp6dW4b+fYMTX3CL7T5jtvpqlF34qIQvvH1JybrjCOAvG+oh+fH+c38lFIhnqxxTFVP0zyuQMAVqJemtxNZhflWKdODqlXJ5aj3vMtLsFGYTyTbTdGEZfH5+V4q+3H7Ge5efCgpzko2ADgfyLuxxrHXmSxijRmD2NmKWYKO1EIxX11MYO4LDF7uGednMbmdSKNVrDF4oPb2vbJOXZJzexX3D83Gw5pXx/NcXhqZgEfS83MWzdjemaOs9t2R8EGAMzY4tRsnVGuiIyZo+UZdQVlPBmhNmyxV5utGbVhxfYq0zmxTgAAjOrdHA+npW+wj1WpyxIzc8POHEVR9kiOe+qBGdimTsyxw+oEAMDKdFT7+kLq7/X2ZPs6SKyS7bb8GCXK/dQAABhB9zSEI1J/tef57esg9Z5mwwYAACugvmE/ZsLiYesAAEyAWN1YLwSImbXyXjYAAOZIbP7aPf+zfFbqemlqEQcAwL/YlnWicneOneskAACz44aiHVt8lDGvGFOwAQDMkd3qxDQUbAAAc+SD1CxcCPUM2/zuTdmuRRsAgFn0eurv4Tad63IsTFO3DwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIBx+xsipgrmyNQNfQAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB0AAAAYCAYAAAAGXva8AAABlUlEQVR4Xu2VzStFQRjGH+X7Y0FhxUZKKZKtDSuUnZCUhKzsbCiuEkUpKbu7I2XjI8rXFsma/AEsKMkGseF5e+d2x9tdqDNXFvdXv7rzvOfMzJmZcy6QIUMaaKKn9Jl+0VvXvqFvrh2jOYkbQrIJHbTaywrorMtXvTwYd/TMhqQGOui9LUSlEdrxpC2QcWhtyxaiMgHtuMHLSmg/fYDucalXC8IxfYHu3xw9gE5CButIXhaOIvpB102+RC9oucmFFnpuQ49iOmBDn07oU42ZvN3lsvSWCtptQ49eemRDn2Vo5/UmT+zzjMl/wwqdsqHPFX2kWSY/QeoVkMns0TaTC3XQc/AKff3mf5aVKmjHO7YAvVlqI669Ad2KZuj+D7ncIqdeBs23BXkvL+knki++DNLqXVNLD+k13Yc+mUxSOntC6gMmdEH7CkoP3aWVNNfUhAU67X7LNUHYhp7cRei3OQ+672WuLqsjJ18+n4Mui8wajdM+15bO3+mwa49C/xxkItkuSwuy/7Lsf0qMFtow3cge/j++AYHFTp9UTssNAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACQAAAAYCAYAAACSuF9OAAAB4UlEQVR4Xu2WzUsVURjGH8OQEheJ7VIQCYREaeVKqGjhB7hSi8BVgRCIG/MLrKBFmrgR/wNDcCEuVMTCjYWIixZRtHBZi9yoIBi20efhPcM9vrdV07234v7gB3Ped86cMzPvOTNAkSL/OTfpW7pPT+mX0P5Mj0P7Gb2YdMgX87AJ1USxS/R5iM9E8bzwlb73QVIHm9A3n8glTbBBR32C9MNyCz6RSwZhgzZGsQr6gH6H1dSVKJdz1ukhrF5e0BXYBDWRtsxp+aGcntA5F39Ft+hVF0+LavKuD8a0w55Gn4u3hrhe559klo75YMw0bOAbLp7U1VMXT8sH2uKDMTt0j5a4+BtkP7lSOhlyvXSILtL7sBsYoZu0KukQcQ+W+wGrTbWzqIYNuuQTsE7KPQrt17QHthK1iw+EeBfdhV1LbNA74dijMtB1s9C+s01/IrPp6cTb0TnX6Rr9RJdhg1yD3f0RMp+Sl7DXLvQED2B9f8UUHffBtHTAJpqg19cZjm/Rj7A9TKvX8w52jm6m8nzq91ENDYdjXVgfZU1ATMDqSPlaWgarQQ1+AVY/+j5qw60PfVKjTbQ5HDfACjXhCV2FTUpoz9EkHoa29rrHtDu0C4LqSYvhr0H/Upd9sJBoqf9bnAFGx1t2w1hfHAAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAiCAYAAADiWIUQAAAEr0lEQVR4Xu3cachtUxzH8aUoMpQylSjzFJEXpOgYkrG8IJKEW+R2eSHz+GRKhEK8oa7pFZLhhTmkTBGFQsoLY5QohMT/Z6919//8z36es/cZ6tj3+6l/e63/2s/z3L3vqf1vrbVPSgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAfjsiHz8dygIAAGBh3JqP/wxlAQAAsHAejAkAADC9ty2usdgp91+2+KEeTpdZHJjb+1q85ca8i9PysyvfhP5nFluFXN/5e7NkcZfrz8P1MTEjuo4dc3sp9+UAi9stds79aTwXEwAArM9UiH0Ycuen+iGsfUmxCNNDuck5afRc2TON5o+3uDnk+u4N197F4ivXn4cbY2JG4nWU/9uHLQ63uKkentgLMQEAwPpKBVMspGQfixty+85UnbN3PdzozHz8ZShbedriz5DbxOKLkIu2S9XfXi6Ork8dcobF7rldZgqvzsdJXWvxeaqKrDJz9W49PJZmH/fL7c0tvrPYsh6ei3GF05EWf1t8YPFazq1N1UzZcpqu48V6eGba/M43Uz3zCwBAb6noeTwmG2yRqiJF5zcVZFe6tmZf9CD39HNLIacC6o7c3swPzICWW4srUlVMxuVH9WMBWOLV+rR1DnbtJy32t9gm98cVXpta/OH62py/teu3oZmso2IyOCWNXouPeJ/Pde2LLC60ODH377d41mK3dWdUpr2OlcR/r4/okFSP/ZVzuj4V6wAA9IoedipoogtiIrs7NT8848N1j+Hh/3KHhpyWYffK7VP9wJQ0O3SP66+xeMdiB5eb1nkWl+S2lh2fcGNNjkvD9+2YVM1UdaFr8oVxG+Nm2Dz9XzxksUHuayn80jT6FR3TXkdb42bYVGxqhtDT54i9bwCA3vnN4r2QO81io9w+2Q+Yey0+CTnNwni3WJzu+tqc/ozri/a0Pebav6ZuxcVKVGiUWSLRUqafHZsFza75/WcD126igvF719f+LBV9he6PXvpQQaz7/1Kq9oIVKkR+T+OLmKjrPf0x9AdptEBf6TraaFtUjbvWkyxOcP3yOfL76wAA6I1dLd5P1fJknMHR26KaZdFm8tdT9VAsNOOjh7dfItNDVoXMtxbbpvrlhY/zmAqR21L1pqk37uHc1SMWr6T66yX0VmubIqEtza6d5foD1470t3UPdF9KEaZlxo9SVVxqGU/3X47Nx6csVuV2oYKuqy4F20EWD4Sc7t/Gua3r0D7EpusoBbmOZ6e68NQSqy88uxRVbT4T+lxq6bbsKWzzMwAAYEIqRlTg/V88n6o9VMXAtSfxUz6WFyN+ttg+t4tBqmc+2+pSsF1lcbnra2lZy6Ntv6JD+xzvS9XMqfa1lf12S+WETAVbKQJXMknxNUlRCwAAWtILABvG5ALT7F2hPXKPptHCpAvNYsqX+ag3Ntem6kUDLYXK6lS9VDAvX6fqzd2i7Ecsf78NFZ4qKkvhqd8XC895FlX6HHVdogUAAJjadTGxwGLheVgaLTwpqgAAQO/oTcw+iF8PAgAAgAXTl8ITAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAi+hf3jzl0WxtaLwAAAAASUVORK5CYII=>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAUCAYAAACEYr13AAAA9ElEQVR4XmNgGAWjAAF4gHg2EH8A4pdAHIUqzbAYiOXRxOCAGYh3AvF/ID4LxB+hbBeovCoQr4WysYJWBogLkAEbEN8CYg4g3oskXgfEu4H4JBC7IYljBUuAuASIU6H8OCCuhrItgfgnEOtA+VhBLRA/AGIBKL8SiI/DZSEurEHiY4A8BogrsAF2IP4KxAlo4igA5HwfdEEoyAbiq0DMhS6BDDYBsSK6IBDoMkACVgZdAhmAnPiKARLFyAAUW4uAmBfKd0BIoQIbID6MJsYIxDMYIN5yAOJwBjxhAArARjQxUJiAEhgytkVRgQR6gFgFXRAbAACReSbHGtmUaQAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,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>