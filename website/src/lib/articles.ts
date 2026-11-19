// Research articles. Numbers appear only in `results`, copied from the published datasets listed in
// `resultsBasedOn`; the article page warns if those datasets have changed since.
// `stage` is an editorial fact (how far the writing and analysis are). Data readiness is
// never set here; it is derived from dataset_status.json (see lib/status.ts).

export interface Reference { authors: string; year: number; title: string; venue: string; doi?: string; url?: string; note?: string }
export interface Hypothesis { id: string; statement: string; test: string }
export interface Variable { name: string; definition: string; dataset: string }
export interface ResultBlock { kind: "observed" | "association" | "model_estimate" | "interpretation" | "causal"; text: string }
// The dataset versions the written results were computed from. The article warns readers if the live data differ.
export interface ResultsBasis { date: string; versions: Record<string, string> }

export interface Article {
  slug: string;
  module: "F1 Moneyball" | "The Cost Cap Paradox" | "The Grand Prix Economy";
  flagship?: boolean;
  title: string;
  dek: string;
  stage: "Research design" | "Research in progress" | "Published";
  author: string;
  draftRevised: string; // date the text was last revised (ISO). Not a publication date.
  publishedOn: string | null; // null until real results are published
  question: string;
  whyItMatters: string[];
  literature: string[];
  hypotheses: Hypothesis[];
  datasets: string[];
  variables: Variable[];
  strategy: string[];
  results: ResultBlock[]; // empty until the pipeline produces real outputs
  resultsBasedOn?: ResultsBasis;
  robustness: string[];
  interpretation: string[];
  limitations: string[];
  reproducibility: string[];
  references: Reference[];
  interactive?: { to: string; label: string };
}

const AUTHOR = "Nahian Ibnat";

export const ARTICLES: Article[] = [
  {
    slug: "does-money-buy-speed",
    module: "F1 Moneyball",
    flagship: true,
    title: "Does Money Buy Speed?",
    dek: "How efficiently do Formula 1 teams convert financial resources into sporting performance?",
    stage: "Published",
    author: AUTHOR,
    draftRevised: "2026-11-19",
    publishedOn: "2026-11-19",
    question:
      "Does spending more money make a Formula 1 team faster, or does competitive success depend on how efficiently a team converts financial resources into on-track performance?",
    whyItMatters: [
      "Formula 1 is a closed league of about ten firms that compete for a fixed set of prizes. Teams choose how much capital to raise and how to spend it, and since 2021 a cost cap limits most of that spending. It is a rare setting where the effect of a spending limit on competition can be studied in a small, well-recorded market.",
      "If money mainly buys speed, a binding cap should compress the field over time. If organisation, engineering choices and execution matter more, the order of teams should depend on how well each one uses what it has. The two answers point to very different policies for leagues that want close competition.",
    ],
    literature: [
      "Sports economics has long asked whether richer teams win more. Rottenberg (1956) and Neale (1964) set out why leagues need some balance, since a contest with a certain winner loses its value. Szymanski (2003) surveys how contest design, including spending rules, shapes effort and outcomes.",
      "In team sports, Hall, Szymanski and Zimbalist (2002) test the direction of causality between payroll and performance. For Major League Baseball they find no evidence that causality runs from payroll to performance over the full sample, while for English football they cannot reject it. Their approach, testing whether past spending predicts later results, guides this study.",
      "In Formula 1, Bell, Smith, Sabel and Jones (2016) show that team effects explain more of results than driver effects, and increasingly so over time. That makes the team, and the resources behind it, the right unit of analysis. Jenkins (2010) shows how major rule changes can reset which teams lead, which matters for any study spanning several regulatory eras.",
    ],
    hypotheses: [
      { id: "H1", statement: "Teams with larger financial resources score a larger share of championship points.", test: "Association between resource share and points share across team-seasons, by regulatory period." },
      { id: "H2", statement: "Within a team, a change in spending is followed by a change in performance only with a lag.", test: "Team fixed-effects models with resources lagged one season." },
      { id: "H3", statement: "The link between resources and points is weaker under the cost cap than before it.", test: "Interaction between resources and a cost-cap period indicator. Descriptive, because all teams were capped at once." },
      { id: "H4", statement: "Holding resources fixed, reliability and race-day execution explain part of the remaining differences.", test: "Adding completion rate, mechanical retirement rate and grid-to-finish gains to the H1 model." },
    ],
    datasets: ["constructor_season", "financial_observation", "efficiency", "model_results", "race_result", "regulation_event"],
    variables: [
      { name: "points_share", definition: "Team points divided by all teams' points in the season. Used instead of raw points because the points system changed.", dataset: "constructor_season" },
      { name: "resource measure", definition: "One clearly named financial measure per chart (for example audited operating costs of the team entity). Different measures are never combined.", dataset: "financial_observation" },
      { name: "financial efficiency ratio", definition: "Points share divided by resource share, computed only among teams with comparable figures in that season. A descriptive ratio, not a measure of technical efficiency.", dataset: "derived" },
      { name: "completion_rate", definition: "Classified finishes divided by car starts.", dataset: "constructor_season" },
      { name: "mean_grid_to_finish", definition: "Average places gained from grid to finish by classified cars.", dataset: "constructor_season" },
      { name: "median_quali_gap_pct", definition: "Median gap of the team's best car to pole, in percent.", dataset: "constructor_season" },
    ],
    strategy: [
      "Step 1, description: plot points share against each available resource measure by season, with every point labelled by its source classification (audited, official disclosure, estimate).",
      "Step 2, pooled and fixed-effects regressions: log points share on log resources, then with team fixed effects, then with team and season fixed effects. Standard errors clustered by team. Resources enter with a one-season lag to reduce reverse causality, since success raises prize money and sponsorship.",
      "Step 3, efficiency: the financial efficiency ratio and a rank-based version (points rank minus resource rank), shown side by side rather than combined into one score.",
      "Step 4, operations: add reliability and race-day measures to the Step 2 model and report how much the resource coefficient and fit change.",
      "Identification: none of these steps identifies a causal effect of spending. Results are reported as associations. Where a model estimate is shown, it is labelled as such.",
    ],
    results: [
      { kind: "observed", text: "Coverage. Audited Companies House accounts exist for six team lineages with UK companies: Red Bull, Mercedes, McLaren, Williams, Enstone (Lotus, Renault, Alpine) and Silverstone (Force India, Racing Point, Aston Martin). Together they give 70 team-seasons from 2014 to 2025 with turnover, staff costs and headcount. Ferrari, Sauber, Racing Bulls and Haas do not file comparable accounts and are not covered." },
      { kind: "association", text: "Among these six teams, a team's share of their combined turnover and its share of their combined points move together: the correlation across the 70 team-seasons is 0.75. In single seasons it ranges from 0.33 (2014) to 0.98 (2021)." },
      { kind: "observed", text: "Average efficiency ratio (points share divided by turnover share), 2014 to 2025: Mercedes 1.48, Red Bull 1.23, Silverstone lineage 1.09, McLaren 0.69, Williams 0.47, Enstone 0.46. In 2025 McLaren had the highest ratio (1.85) and Enstone the lowest (0.10)." },
      { kind: "model_estimate", text: "Pooled model: 10% more turnover in the previous season goes with a points share about 1.0 percentage point higher (coefficient 0.108 on log turnover, 95% CI 0.058 to 0.159). Staff costs and headcount give similar pooled results (about 1.6 points each)." },
      { kind: "model_estimate", text: "With team fixed effects the turnover link almost disappears: 0.009 (95% CI -0.093 to 0.111, p = 0.87). With team and season fixed effects it is 0.020 (p = 0.60). Headcount behaves the same way. Most of the pooled link comes from lasting differences between teams, not from a team doing better in the years when it had more money." },
      { kind: "model_estimate", text: "Staff costs are the exception. With team and season fixed effects the coefficient is 0.288 (95% CI 0.046 to 0.531, p = 0.02), about 2.7 percentage points of points share per 10% more staff spending. The result is fragile: with team fixed effects alone it is 0.061 (p = 0.41), and the standard errors rest on only six team clusters." },
      { kind: "association", text: "Pit stop operations: teams with higher turnover had faster pit stops relative to the fastest team in the same race (Spearman rank correlation -0.48 across the same 70 team-seasons). Each team appears up to 12 times, so this is a description, not a test." },
    ],
    resultsBasedOn: { date: "2026-11-19", versions: { financial_observation: "22bb6565b17e", efficiency: "dc3323619a40", model_results: "a4ef1b5f7497", constructor_season: "e94cc086e8e9" } },
    robustness: [
      "Alternative financial measures (operating costs, staff costs, turnover), each in its own model.",
      "Team lineage treated as continuous through rebrands versus each rebrand as a new team.",
      "Excluding seasons with large rule resets (2014, 2017, 2022).",
      "Points share versus championship position as the outcome.",
      "Restricting to teams with audited figures only.",
    ],
    interpretation: [
      "H1 holds as a description: among the teams covered, richer teams score more points. H2 does not: within a team, more money in one season does not reliably come before more points in the next. This fits a picture in which money and success build up together over many years, since winning teams earn more prize money and attract more sponsors, rather than one in which extra spending quickly buys points.",
      "The staff-cost result is the one sign of a within-team link, but it disappears in the simpler fixed-effects model and needs more teams or seasons before it can carry weight.",
      "H3 (a weaker link under the cost cap) and H4 (reliability and race-day execution) have not been tested in a model yet. The Cost Cap Paradox study looks at the cap from the side of competitive balance.",
      "None of these results is a causal effect of spending.",
    ],
    limitations: [
      "Only six teams are covered, so every estimate uses six clusters and confidence intervals may be too narrow.",
      "The financial panel is small and unbalanced: statutory accounts exist mainly for UK-registered entities, and Ferrari does not file comparable accounts.",
      "Accounts belong to legal entities, not teams. An entity may include engine work or other business, or leave out costs held elsewhere in a group.",
      "Accounting periods, currencies and accounting standards differ across teams and years.",
      "Reverse causality: good results bring prize money and sponsors, which raise later spending.",
      "With team and season fixed effects, the resource coefficient relies on small within-team changes and will be imprecise.",
    ],
    reproducibility: [
      "Sporting data: python -m f1moneyball.pipeline all (Jolpica-F1 API, rate-limited and cached).",
      "Financial data: data/manual/financial_observations.csv, validated by python -m f1moneyball.pipeline validate.",
      "Models: src/f1moneyball/econometrics/models.py and efficiency.py; outputs in the model_results and efficiency datasets.",
    ],
    references: [
      { authors: "Rottenberg, S.", year: 1956, title: "The baseball players' labor market", venue: "Journal of Political Economy, 64(3), 242–258" },
      { authors: "Neale, W. C.", year: 1964, title: "The peculiar economics of professional sports", venue: "Quarterly Journal of Economics, 78(1), 1–14" },
      { authors: "Hall, S., Szymanski, S., & Zimbalist, A. S.", year: 2002, title: "Testing causality between team performance and payroll: The cases of Major League Baseball and English soccer", venue: "Journal of Sports Economics, 3(2), 149–168", doi: "10.1177/152700250200300204" },
      { authors: "Szymanski, S.", year: 2003, title: "The economic design of sporting contests", venue: "Journal of Economic Literature, 41(4), 1137–1187" },
      { authors: "Jenkins, M.", year: 2010, title: "Technological discontinuities and competitive advantage: A historical perspective on Formula 1 motor racing 1950–2006", venue: "Journal of Management Studies, 47(s1), 884–910" },
      { authors: "Bell, A., Smith, J., Sabel, C. E., & Jones, K.", year: 2016, title: "Formula for success: Multilevel modelling of Formula One driver and constructor performance, 1950–2014", venue: "Journal of Quantitative Analysis in Sports, 12(2), 99–112", doi: "10.1515/jqas-2015-0050" },
    ],
    interactive: { to: "/moneyball", label: "Open the F1 Moneyball laboratory" },
  },
  {
    slug: "cost-cap-paradox",
    module: "The Cost Cap Paradox",
    title: "The Cost Cap Paradox",
    dek: "Did the introduction of the Formula 1 cost cap change competitive balance?",
    stage: "Published",
    author: AUTHOR,
    draftRevised: "2026-11-19",
    publishedOn: "2026-11-19",
    question: "Did the introduction of the Formula 1 cost cap change competitive balance?",
    whyItMatters: [
      "The cost cap was introduced in 2021 partly to make the championship more competitive and partly to keep teams financially stable. Whether it changed competitive balance is a direct test of a spending rule in a real league.",
    ],
    literature: [
      "Judde, Booth and Brooks (2013) study competitive balance in Formula 1 from 1950 to 2010, including the earlier Resource Restriction Agreement on team spending. They find that regulation change had a significant positive effect on championship uncertainty, but not on race uncertainty or long-term dominance. Mastromarco and Runkel (2009) also study how rule changes affect balance in Formula 1.",
      "Budzinski and Feddersen (2020) separate three dimensions of balance in Formula 1: within a race, within a season and between seasons. This study follows that split. Owen, Ryan and Weatherston (2007) show that the HHI depends on the number of teams, and Utt and Fort (2002) set out pitfalls of the Gini coefficient. Both shape the choice of indicators here.",
    ],
    hypotheses: [
      { id: "H1", statement: "Concentration of championship points is lower after 2021 than before.", test: "Normalized HHI, Gini and top-3 share by season, compared across regulatory periods." },
      { id: "H2", statement: "Team order changes more between seasons after 2021.", test: "Rank persistence and mean absolute rank change." },
      { id: "H3", statement: "Teams that had to cut spending most lost ground relative to others.", test: "Dose-response comparison using audited pre-2021 spending. Suggestive only." },
    ],
    datasets: ["competitive_balance", "regulation_event", "cost_cap_models", "cost_cap_event_study", "constructor_season", "financial_observation"],
    variables: [
      { name: "hhi_normalized", definition: "HHI of points shares, rescaled so 0 = equal shares and 1 = one team scores everything.", dataset: "competitive_balance" },
      { name: "gini", definition: "Gini coefficient of constructor points.", dataset: "competitive_balance" },
      { name: "top3_share", definition: "Points share of the best three teams.", dataset: "competitive_balance" },
      { name: "rank_persistence", definition: "Spearman correlation of team rank with the previous season.", dataset: "competitive_balance" },
    ],
    strategy: [
      "Descriptive comparison of balance indicators across regulatory periods.",
      "Interrupted time series: y_t = a + b·trend + c·post2021 + d·post2021·(t − 2021), Newey-West standard errors. Specification B adds a 2022 technical-reset dummy, which leaves the 2021 change identified from one season.",
      "Placebo break years inside the pre-cap period: how often does a fake break produce a change as large as 2021?",
      "Dose-response comparison: points share on exposure × post with team and season effects, where exposure is the standardised log of pre-cap (2018–2020) resources; event study by season with 2020 as reference to check pre-trends. Reported as suggestive.",
    ],
    results: [
      { kind: "observed", text: "Average balance before (2010 to 2020) and under the cap (2021 to 2025): normalized HHI of points 0.127 and 0.115; Gini 0.574 and 0.532; top-three share 0.723 and 0.706; leader's points share 0.321 and 0.303. Every measure points slightly towards a closer field, and every change is small." },
      { kind: "observed", text: "Team order moved a little more under the cap: the rank correlation with the previous season averaged 0.842 before and 0.787 after, and the average change in a team's position rose from 1.16 to 1.52 places." },
      { kind: "model_estimate", text: "Interrupted time series for normalized HHI: level change at 2021 of -0.008 (95% CI -0.027 to 0.011, p = 0.39). In 4 of the 6 placebo break years (2013 to 2018) the model finds a change at least as large, so 2021 does not stand out." },
      { kind: "model_estimate", text: "The leader's points share drops by 0.056 at 2021 (p = 0.008), but placebo breaks in 2017 and 2018 give drops of similar size (0.061 and 0.058). Gini and top-three share show no clear change (p = 0.15 and 0.74)." },
      { kind: "model_estimate", text: "Rank persistence: the time-series model gives a level increase of 0.088 at 2021 (p = 0.02), the opposite sign to the simple averages above. The model result depends on the pre-cap trend and should not be read on its own." },
      { kind: "model_estimate", text: "Dose-response: teams with one standard deviation more pre-cap turnover (2018 to 2020 average) changed their points share by 0.009 after 2021 relative to others (95% CI -0.072 to 0.089, p = 0.83). In the event study, only 2019 differs from the 2020 reference before the cap (0.023, 95% CI 0.001 to 0.046)." },
    ],
    resultsBasedOn: { date: "2026-11-19", versions: { competitive_balance: "737f103cf04f", cost_cap_models: "6b1276a8dddc", cost_cap_event_study: "5d51f60d7441" } },
    robustness: ["Alternative indicators", "Excluding 2020 and 2021 (COVID-19 calendars)", "Placebo years"],
    interpretation: [
      "In its first five seasons there is no evidence that the cost cap changed competitive balance. The changes after 2021 point towards a slightly closer field, but they are about the size of normal swings from year to year, as the placebo years show.",
      "H1 (lower concentration) is not supported beyond a small descriptive drop. H2 (more movement in team order) gets mixed evidence: the averages say yes, the time-series model says no. H3 (big spenders lose ground) is not supported: the dose-response estimate is close to zero.",
      "This does not show that the cap had no effect. With five capped seasons, no uncapped teams to compare against and the 2022 technical reset at the same time, only a large effect could have been detected.",
    ],
    limitations: [
      "The dose-response comparison uses turnover for the six teams with UK accounts only.",
      "The 2021 cost cap and the 2022 technical regulations overlap in time. A simple before-and-after comparison cannot isolate the effect of the cap.",
      "All teams were subject to the cap, so there is no untreated control group.",
      "Only five capped seasons with comparable rules (2021 to 2025), so tests have low power.",
      "COVID-19 changed calendars, revenue and car development rules in 2020 and 2021.",
    ],
    reproducibility: ["python -m f1moneyball.pipeline all", "Indicators: src/f1moneyball/feature_engineering/competitive_balance.py"],
    references: [
      { authors: "Utt, J., & Fort, R.", year: 2002, title: "Pitfalls to measuring competitive balance with Gini coefficients", venue: "Journal of Sports Economics, 3(4), 367–373" },
      { authors: "Owen, P. D., Ryan, M., & Weatherston, C. R.", year: 2007, title: "Measuring competitive balance in professional team sports using the Herfindahl-Hirschman index", venue: "Review of Industrial Organization, 31(4), 289–302", doi: "10.1007/s11151-008-9157-0" },
      { authors: "Mastromarco, C., & Runkel, M.", year: 2009, title: "Rule changes and competitive balance in Formula One motor racing", venue: "Applied Economics, 41(23), 3003–3014" },
      { authors: "Judde, C., Booth, R., & Brooks, R.", year: 2013, title: "Second place is first of the losers: An analysis of competitive balance in Formula One", venue: "Journal of Sports Economics, 14(4), 411–439", doi: "10.1177/1527002513496009" },
      { authors: "Budzinski, O., & Feddersen, A.", year: 2020, title: "Measuring competitive balance in Formula One racing", venue: "In P. Rodríguez, S. Késenne & B. R. Humphreys (Eds.), Outcome Uncertainty in Sporting Events (pp. 5–26). Edward Elgar" },
    ],
    interactive: { to: "/cost-cap", label: "Open the Cost Cap explorer" },
  },
  {
    slug: "grand-prix-economy",
    module: "The Grand Prix Economy",
    title: "Who Gains When Formula 1 Comes to Town?",
    dek: "Does hosting a Formula 1 Grand Prix generate net additional economic benefits for the host economy?",
    stage: "Published",
    author: AUTHOR,
    draftRevised: "2026-11-19",
    publishedOn: "2026-11-19",
    question: "Does hosting a Formula 1 Grand Prix generate net additional economic benefits for the host economy?",
    whyItMatters: [
      "Governments often pay hosting fees and public costs to bring a Grand Prix to their city, and justify this with headline economic impact figures. Those figures usually count gross spending, not the extra activity the race actually causes.",
    ],
    literature: [
      "Coates and Humphreys (2008) review the evidence on public subsidies for sports facilities and mega-events and find that economists broadly doubt that the benefits justify the subsidies. Baade and Matheson (2004) show for the football World Cup that promoters' forecasts tend to overstate the impact.",
      "Henderson, Foo, Lim and Yip (2010) study the Singapore Grand Prix as a tourism event. Abadie, Diamond and Hainmueller (2010) develop the synthetic control method, which builds a comparison region from similar places that did not host the event.",
    ],
    hypotheses: [
      { id: "H1", statement: "Visitor arrivals in the race month rise above what comparable regions would predict.", test: "Event study and synthetic control on monthly arrivals." },
      { id: "H2", statement: "Part of the race-month rise is offset by fewer visitors in nearby months (displacement).", test: "Pre- and post-race month effects." },
    ],
    datasets: ["gp_tourism_monthly", "gp_race_events", "gp_event_study", "gp_scm_path", "gp_scm_inference"],
    variables: [
      { name: "arrivals", definition: "Guest arrivals at accommodation establishments per month and federal state, all accommodation types (Statistik Austria).", dataset: "gp_tourism_monthly" },
      { name: "overnight stays", definition: "Nights spent at accommodation establishments per month and federal state, all accommodation types (Statistik Austria).", dataset: "gp_tourism_monthly" },
    ],
    strategy: [
      "Separate gross activity, direct spending, indirect effects, displacement, leakage and net additional benefit.",
      "Event study for each host separately: log monthly series on month-of-year effects, a trend and dummies for two months before to two months after each race month, HAC standard errors.",
      "Synthetic control for the race's entry to the calendar: non-negative donor weights summing to one, fitted on pre-entry months; inference by placebo-in-space (rank of the post/pre RMSPE ratio). If pre-entry fit is poor (RMSPE above 0.10 log points), the gap is not read as an effect.",
    ],
    results: [
      { kind: "observed", text: "First host studied: Styria, home of the Austrian Grand Prix at the Red Bull Ring since F1 returned in June 2014. Data: monthly arrivals and overnight stays for all nine Austrian federal states, 2008 to 2025, from Statistik Austria. The analysis stops in December 2019 because COVID-19 closures from March 2020 moved tourism far more than any race, so six race years (2014 to 2019) are used." },
      { kind: "model_estimate", text: "Event study: in race months, arrivals in Styria were 13.3% higher than in the same calendar month of other years after a linear trend (95% CI 8.7% to 18.0%). Overnight stays were 10.0% higher (95% CI 5.7% to 14.5%)." },
      { kind: "model_estimate", text: "The two months after the race were also higher (arrivals +7.6% and +6.5%), while the two months before were not (-0.9% and +2.0%, both within their confidence intervals of zero)." },
      { kind: "model_estimate", text: "Synthetic control: a weighted mix of Lower Austria (0.32), Salzburg (0.29), Upper Austria (0.20), Vorarlberg (0.10), Tyrol (0.04) and Vienna (0.04) tracked Styria's arrivals closely before June 2014 (pre-entry RMSPE 0.069 log points, under the 0.10 rule). After 2014, Styria was on average only 0.6% above its synthetic version. Its post/pre RMSPE ratio (0.91) is smaller than that of 7 of the 8 placebo states (p = 0.89). For overnight stays the gap is +2.1% (p = 0.44)." },
    ],
    resultsBasedOn: { date: "2026-11-19", versions: { gp_tourism_monthly: "b5d0083b403f", gp_event_study: "49bc9cde2312", gp_scm_inference: "6a9e34197817" } },
    robustness: ["Different comparison pools", "Excluding COVID-19 years", "Placebo race months"],
    interpretation: [
      "Race months in Styria are busier than usual, but the region as a whole did not gain visitors relative to a comparable mix of Austrian states after the race returned. H1 holds only in this narrow, month-level sense.",
      "H2 (displacement) is not supported in the expected form: the months before the race show no drop. The months after the race are also higher, which looks more like a general rise in Styria's summer tourism than an effect of one race weekend. MotoGP has raced at the same circuit every August since 2016, which adds to the summer months.",
      "These figures count visitors, not spending, hosting fees or public costs, so they cannot say whether hosting is a good deal for the region.",
    ],
    limitations: [
      "Only one host region so far (Styria). Singapore is planned but supports only the event study, since there are no clean comparison countries.",
      "Several placebo states fit poorly before 2014 (Burgenland, Carinthia, Tyrol, Vienna, Vorarlberg). The RMSPE ratio used for the p-value adjusts for this in part.",
      "A rise in visitor numbers during a race weekend does not show that the race caused it.",
      "Hosting fees and subsidies are often not disclosed and will be shown only where officially published.",
      "Each host economy is a separate setting; results do not transfer between them.",
    ],
    reproducibility: [
      "Austria inputs: python -m f1moneyball.ingestion.statistik_austria (reads the Statistik Austria open data files in data/source_documents/statistik_austria).",
      "Models: src/f1moneyball/econometrics/gp_economy.py, run by python -m f1moneyball.pipeline publish.",
    ],
    references: [
      { authors: "Baade, R. A., & Matheson, V. A.", year: 2004, title: "The quest for the cup: Assessing the economic impact of the World Cup", venue: "Regional Studies, 38(4), 343–354" },
      { authors: "Coates, D., & Humphreys, B. R.", year: 2008, title: "Do economists reach a conclusion on subsidies for sports franchises, stadiums, and mega-events?", venue: "Econ Journal Watch, 5(3), 294–315" },
      { authors: "Abadie, A., Diamond, A., & Hainmueller, J.", year: 2010, title: "Synthetic control methods for comparative case studies: Estimating the effect of California's tobacco control program", venue: "Journal of the American Statistical Association, 105(490), 493–505" },
      { authors: "Henderson, J. C., Foo, K., Lim, H., & Yip, S.", year: 2010, title: "Sports events and tourism: The Singapore Formula One Grand Prix", venue: "International Journal of Event and Festival Management, 1(1), 60–73", doi: "10.1108/17852951011029306" },
    ],
    interactive: { to: "/grand-prix-economy", label: "Open the Grand Prix Economy page" },
  },
];

export const articleBySlug = (slug: string) => ARTICLES.find((a) => a.slug === slug);
