import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { Callout, PageHeader, Section } from "../components/Ui";

// Plain-language answers to the questions readers ask most. No estimates are written here:
// results live in the articles, which carry their dataset versions. This page explains words and choices.

const PAPER = "papers/Ibnat_Does_Money_Buy_Speed_working_paper.pdf";
const REPO = "https://github.com/NahianIbnat-2000/F1-moneyball";

interface QA { id: string; q: string; a: ReactNode; text: string }
interface Group { id: string; title: string; items: QA[] }

// `text` is the same answer as plain text, used for the search engine summary (FAQPage schema).
const qa = (id: string, q: string, a: ReactNode, text: string): QA => ({ id, q, a, text });

const GROUPS: Group[] = [
  {
    id: "big-questions",
    title: "The big questions",
    items: [
      qa("does-money-buy-speed", "So, does money buy speed?",
        <>
          <p>Partly. Across teams, money and results go together strongly: the richest teams win most. Within a single team over time, the link is much smaller. Once you remove what happens to every team in the same season, more spending, especially on staff, comes before modestly better results the next season. With eight teams this is suggestive, not proof.</p>
          <p>For the numbers, see the <Link to="/research/does-money-buy-speed">research article</Link> or the <a href={PAPER}>working paper</a>.</p>
        </>,
        "Partly. Across teams, money and results go together strongly. Within a single team over time the link is much smaller: more spending, especially on staff, comes before modestly better results the next season. With eight teams this is suggestive, not proof."),
      qa("causal", "Does this prove that spending more makes a team faster?",
        <p>No. Every result here is an <em>association</em>: two things that move together. Good results bring prize money and sponsors, so success can raise spending as well as the other way round. Using last season's money reduces this problem but does not remove it. Showing that money <em>causes</em> speed would need something like a rule change that gave some teams more money for reasons unrelated to how good they were. F1 has no such clean experiment.</p>,
        "No. Every result is an association. Success brings money, so the direction can run both ways. Using last season's money reduces this but does not remove it."),
      qa("why-it-matters", "Why does this matter outside Formula 1?",
        <p>F1 teams are firms that compete for a fixed set of prizes, which makes the sport a clear case study of a wider economic question: does spending buy an advantage, or does it matter more how well an organisation uses what it has? The same question comes up with research budgets, payrolls in other sports, and spending caps in regulated industries.</p>,
        "F1 is a clear case study of whether spending buys an advantage or whether how well an organisation uses its money matters more."),
      qa("cost-cap-short", "Did the cost cap make F1 more equal?",
        <p>Not in a way the data can confirm yet. The change after 2021 cannot be told apart from the changes seen in years with no policy change. A big technical rule change arrived in 2022, one season after the cap, so the two cannot be separated with season-level data. See <Link to="/research/cost-cap-paradox">The Cost Cap Paradox</Link>.</p>,
        "Not in a way the data can confirm yet. The change after 2021 cannot be told apart from changes in years with no policy change, and the 2022 technical rules arrived one season later."),
      qa("gp-short", "Does hosting a Grand Prix bring more tourists?",
        <p>The evidence is weak. In Styria, home of the Austrian Grand Prix, the race month has more visitors than usual, but much less once you compare with the rest of Austria, and the comparison method cannot separate it from chance. Singapore shows no clear rise in its race month. See <Link to="/research/grand-prix-economy">The Grand Prix Economy</Link>.</p>,
        "The evidence is weak. Styria's race month has more visitors than usual but much less compared with the rest of Austria; Singapore shows no clear rise."),
    ],
  },
  {
    id: "money-terms",
    title: "Money terms",
    items: [
      qa("turnover", "What is turnover?",
        <p>Turnover is a company's total income in a year from its business: prize money, sponsorship, payments from its owner, and selling parts or services to other teams. It is the UK word for revenue. It is not profit. In this project it stands for how much money a team had available.</p>,
        "Turnover is a company's total income in a year, the UK word for revenue. It is not profit."),
      qa("staff-costs", "What are staff costs?",
        <p>Everything the company paid its employees in the year: wages and salaries, social security (National Insurance) and pension costs. It is the clearest measure of spending on people, which is most of what an F1 team does.</p>,
        "Everything the company paid its employees in a year: wages, social security and pension costs."),
      qa("headcount", "What is headcount?",
        <p>The average number of people employed during the year, as reported in the accounts. It measures size in people rather than in pounds, so it is not affected by inflation or exchange rates.</p>,
        "The average number of people employed during the year, as reported in the accounts."),
      qa("audited-accounts", "What are audited accounts, and why use them?",
        <p>Every UK company must file yearly accounts with <a href="https://find-and-update.company-information.service.gov.uk/">Companies House</a>, the UK's public register of companies. For large companies an independent auditor checks them. They are the most reliable public source of a team's finances, much better than press estimates. Every figure here links to the filing it came from.</p>,
        "Yearly accounts that UK companies file with Companies House, checked by an independent auditor. They are the most reliable public source of team finances."),
      qa("why-gbp", "Why are the figures in pounds and not adjusted for inflation?",
        <p>The accounts are reported in pounds, and the figures are shown exactly as filed so they can be checked against the source. Inflation is handled in the models instead: comparing teams within the same season removes anything that affects every team that year, including inflation. The simple comparisons across all years do not adjust for it, and the paper says so.</p>,
        "Figures are shown as filed in pounds. Season effects in the models remove inflation; the simple pooled comparison does not."),
      qa("cost-cap", "What is the cost cap?",
        <p>Since 2021 the FIA Financial Regulations limit how much most F1 teams can spend in a year: a base of USD 145 million in 2021, 140 million in 2022 and 135 million from 2023, adjusted for the number of races. Some costs are left out, including driver pay, the pay of the three highest-paid staff, and power-unit (engine) supply up to a set price. So a team's total spending can be well above the cap.</p>,
        "Since 2021 the FIA limits most team spending: USD 145 million in 2021, 140 million in 2022 and 135 million from 2023, with some costs such as driver pay excluded."),
      qa("financial-year", "A team's financial year does not match the racing season. How is that handled?",
        <p>Each set of accounts is matched to the season it mostly covers, and the matching is recorded in the data next to every figure. Where a period was unusual, such as an 18-month period, the figure is kept and flagged with a warning rather than adjusted by hand.</p>,
        "Each set of accounts is matched to the season it mostly covers; unusual periods are flagged rather than adjusted."),
    ],
  },
  {
    id: "performance-terms",
    title: "Performance terms",
    items: [
      qa("points-share", "What is points share?",
        <p>A team's championship points as a share of the points scored by all the teams compared that season. It is used instead of raw points because the points system and the number of races changed over time, so 100 points in 2012 and 100 points in 2024 do not mean the same thing.</p>,
        "A team's points as a share of all points scored by the teams compared that season. It allows fair comparison across years with different points systems."),
      qa("efficiency-ratio", "What is the points-to-turnover-share ratio?",
        <p>A team's share of the points scored by the compared teams, divided by its share of their turnover. A ratio of 1 means the team took the same share of points as of turnover. A ratio of 1.4 means its share of points was 40% larger than its share of turnover; 0.7 means 30% smaller. The same ratio can be computed with staff costs or headcount instead of turnover, so the general name is the points-to-resource-share ratio. It describes outcomes and does not say why they happened. Earlier versions of this site called it the efficiency ratio; that name was dropped because the ratio does not measure efficiency in the economic sense.</p>,
        "A team's share of points divided by its share of turnover. 1 means the two shares are equal."),
      qa("lineage", "What is a team lineage?",
        <p>F1 teams often change name and owner while keeping the same factory and staff. A lineage follows the same organisation through those changes. For example, the team based at Silverstone raced as Force India, then Racing Point, then Aston Martin. The Enstone team raced as Renault, Lotus and Alpine.</p>,
        "The same organisation followed through name changes, for example Force India, Racing Point and Aston Martin."),
      qa("competitive-balance", "What is competitive balance?",
        <p>How evenly success is spread across teams. The cost cap study uses several measures: how concentrated points are (the Herfindahl-Hirschman index and the Gini coefficient), the share of points won by the top three teams and by the leader, and how much the order of teams stays the same from one season to the next.</p>,
        "How evenly success is spread across teams, measured by points concentration, the top teams' share and how stable the order of teams is."),
    ],
  },
  {
    id: "method-terms",
    title: "Method terms",
    items: [
      qa("pooled-vs-fe", "What is the difference between \"between teams\" and \"within teams\"?",
        <p><strong>Between teams</strong> (the pooled model) compares different teams: do richer teams score more? <strong>Within teams</strong> (fixed effects) compares each team only with itself in other years: does a team do better in seasons after it had more money than usual? The two can give very different answers, because rich teams may also be well run for reasons that have nothing to do with a particular year's budget.</p>,
        "Between teams compares different teams. Within teams compares each team with itself in other years."),
      qa("fixed-effects", "What are team and season fixed effects?",
        <p><strong>Team fixed effects</strong> remove everything about a team that stays the same over time, such as its history, location or culture, so the model only uses changes within each team. <strong>Season fixed effects</strong> remove everything that hits every team in the same year, such as inflation, new rules or a change in prize money. Using both is the main within-team test in this project, because points shares add up to one every season while spending rises for almost everyone.</p>,
        "Team fixed effects remove what stays the same about a team; season fixed effects remove what affects every team in the same year."),
      qa("lag", "Why use last season's money?",
        <p>Money from this season partly comes from this season's results, through prize money and sponsors. Using the previous season's money means the spending happened before the results being explained. It reduces this two-way problem but does not remove it.</p>,
        "Using the previous season's money means spending happened before the results. It reduces, but does not remove, the two-way link."),
      qa("p-value", "What does a p-value mean here?",
        <p>A p-value answers: if there were really no link, how often would we see an estimate at least this large just by chance? A small value, such as below 0.05, means the result would be unusual by chance alone. It does not tell you how large or important the effect is, and it does not prove cause.</p>,
        "How often an estimate at least this large would appear by chance if there were no real link. It does not measure size or prove cause."),
      qa("bootstrap", "What is the wild cluster bootstrap, and why is it used?",
        <p>With only eight teams, the usual formulas for p-values can make results look more certain than they are. The wild cluster bootstrap checks this by re-running the analysis on 9,999 simulated versions of the data. In each one, the part of every team's results that the model does not explain is randomly flipped and rescaled, with all of a team's seasons changed together. It gives more trustworthy p-values when there are few groups. Where it and the usual method disagree, the site says so.</p>,
        "A re-sampling method that gives more trustworthy p-values when there are few teams, by re-running the analysis on 9,999 simulated versions of the data, with each team's seasons kept together."),
      qa("leave-one-out", "What is a leave-one-out check?",
        <p>The analysis is repeated eight times, each time without one of the teams. If a result depends on one unusual team, such as Mercedes during its winning years, this shows it.</p>,
        "The analysis is repeated without each team in turn, to see whether one team drives the result."),
      qa("its", "What is an interrupted time series?",
        <p>A way to ask whether a trend changed at a certain date. For the cost cap, it checks whether competitive balance jumped or changed direction in 2021 compared with its path before. Since every team was capped at the same time, there is no group to compare with, so the result is descriptive.</p>,
        "A method that checks whether a trend jumped or changed direction at a certain date, here 2021."),
      qa("placebo", "What is a placebo test?",
        <p>The same analysis run at a date when nothing happened. If fake dates often show changes as large as the real one, the real change is not unusual. The cost cap and Grand Prix studies both use placebo tests.</p>,
        "The same analysis at a date or place where nothing happened, to see whether the real result is unusual."),
      qa("event-study", "What is an event study?",
        <p>A comparison of the months around an event with the usual pattern. For the Grand Prix study, it compares tourist arrivals in the race month and the months either side with the same calendar months in other years, after allowing for the long-term trend.</p>,
        "A comparison of the months around an event with the usual seasonal pattern."),
      qa("synthetic-control", "What is a synthetic control?",
        <p>A way to build a comparison for a place that hosts a race. It combines other regions that did not host, weighted so that together they matched the host's tourism before the race arrived. After the race, the gap between the host and this "synthetic" version is the estimate. Comparison regions are always from the same country as the host.</p>,
        "A weighted mix of non-host regions that matched the host before the race; the gap afterwards is the estimate."),
    ],
  },
  {
    id: "data-and-coverage",
    title: "Data and coverage",
    items: [
      qa("why-eight", "Why only eight teams? Where is Ferrari?",
        <p>Only teams run by a UK company file detailed public accounts at Companies House. Ferrari's F1 team is part of Ferrari N.V., an Italian group, and does not publish comparable team accounts. Sauber, Haas and Racing Bulls do not file comparable UK accounts either. Using press estimates for them would mix reliable and unreliable figures, so they are left out.</p>,
        "Only teams run by UK companies file detailed public accounts. Ferrari, Sauber, Haas and Racing Bulls do not, and press estimates are not used."),
      qa("why-austria-singapore", "Why Austria and Singapore? Why not Hungary or another race?",
        <p>To see whether a race brings tourists, you need a "before": years when the place had no race. So the study only uses hosts where the race started or came back during the years with data. The Austrian Grand Prix in Styria returned in 2014 after ten years away, and the regional data starts in 2008. Singapore's first race was in 2008, and its data starts in 2005. Hungary has hosted a race every year since 1986, so there is no "before". The two hosts are not compared with each other: each is compared with its own past, and Styria also with the rest of Austria. Singapore is a city-state, so it has no other regions to compare with.</p>,
        "The study needs years without a race to compare with. Austria's race returned in 2014 (data from 2008) and Singapore's began in 2008 (data from 2005). Hungary has hosted every year since 1986, so there is no before."),
      qa("eight-enough", "Are eight teams enough?",
        <p>Enough to describe the pattern clearly, but not enough for confident within-team conclusions. This is the main limit of the study, and it is why every within-team result is called suggestive and checked with methods built for few groups.</p>,
        "Enough to describe the pattern, not enough for confident within-team conclusions. It is the study's main limit."),
      qa("sources", "Where does the data come from?",
        <p>Team finances: Companies House filings. Race results and standings: the <a href="https://api.jolpi.ca/ergast/f1/">Jolpica-F1 API</a>, the successor to the Ergast database. Cost cap and technical rules: FIA regulation documents. Tourism: Statistik Austria and the Singapore government's official statistics. Every dataset, with a link to each source, is in the <Link to="/data">Data Explorer</Link>.</p>,
        "Companies House filings, the Jolpica-F1 API, FIA regulations, Statistik Austria and Singapore's official statistics."),
      qa("updates", "How often is the data updated?",
        <p>Race data is refreshed automatically every Monday. Financial figures are added by hand when teams file new accounts. UK companies have up to nine months after their year ends to file, so a year's accounts usually appear by the following autumn. Every update is checked automatically before it is published, and the working paper is rebuilt from the new data each time.</p>,
        "Race data updates every Monday; financial figures when teams file new accounts. Checks run before anything is published."),
      qa("error", "I found an error. What should I do?",
        <p>Please open an issue on <a href={`${REPO}/issues`}>GitHub</a> with the figure, the page where you saw it, and the source you are comparing with. Corrections are listed in the <Link to="/changelog">Changelog</Link>.</p>,
        "Open an issue on GitHub with the figure, the page and your source. Corrections are listed in the Changelog."),
      qa("reuse", "Can I use the data or code?",
        <p>Yes. All datasets can be downloaded from the <Link to="/data">Data Explorer</Link>, and the code is on <a href={REPO}>GitHub</a> under its licence. Please cite the project, and check the original sources' terms for the underlying data.</p>,
        "Yes. Data downloads are in the Data Explorer and the code is on GitHub. Please cite the project."),
    ],
  },
  {
    id: "about-project",
    title: "About the project",
    items: [
      qa("who", "Who made this? Is it connected to F1, the FIA or a university?",
        <p>F1 Moneyball is a personal, independent research project by Nahian Ibnat, an economist with a background in economics, data science and finance. It is not connected to Formula 1, the FIA, any team or any university.</p>,
        "A personal, independent project by Nahian Ibnat, not connected to Formula 1, the FIA, any team or any university."),
      qa("studied-before", "Has this been studied before? What is new here?",
        <>
          <p>Yes, all three questions have been studied before, and the articles discuss that work. The closest is Loník and Kotrba (2024, <em>Managerial and Decision Economics</em>), who find that F1 budgets are linked to better results over 2010 to 2020. Student theses have looked at the cost cap and found no clear change in competitive balance so far. Ramasamy and Yeung (2020) find that hosting a Grand Prix raises a country's tourist arrivals by about 6% on average.</p>
          <p>What this project adds: money measures from audited company accounts that can each be traced to a filing; a split between comparing different teams and comparing each team with itself, which give very different answers; methods built for having only a few teams; data that runs into the cost-cap years; and a regional view of Grand Prix tourism instead of whole countries. Everything is public, so it can be checked and rerun.</p>
        </>,
        "Yes. Loník and Kotrba (2024) link F1 budgets to results for 2010 to 2020; theses study the cost cap; Ramasamy and Yeung (2020) study Grand Prix tourism by country. This project adds audited data, a between- versus within-team split, few-team inference, cost-cap years and a regional tourism view."),
      qa("peer-review", "Is the research peer reviewed?",
        <p>No. The <a href={PAPER}>paper</a> is a working paper: a finished study shared before peer review, which is the usual way economists share research for feedback. That is why the data and code are fully public, so anyone can check the work.</p>,
        "No. It is a working paper, a study shared before peer review. Data and code are public so anyone can check it."),
      qa("cite", "How do I cite it?",
        <>
          <p>It depends on what you use. For the working paper (Study 01):</p>
          <p className="font-mono text-sm">Ibnat, N. (2026). <em>Does money buy speed? Financial resources and sporting performance in Formula 1, 2010 to 2025</em> [Working paper]. F1 Moneyball. https://nahianibnat-2000.github.io/F1-moneyball/papers/Ibnat_Does_Money_Buy_Speed_working_paper.pdf</p>
          <p>For the cost cap or Grand Prix study, the data, or the project as a whole:</p>
          <p className="font-mono text-sm">Ibnat, N. (2026). <em>F1 Moneyball: An independent Formula 1 economics and finance research platform</em> [Website]. https://nahianibnat-2000.github.io/F1-moneyball/</p>
        </>,
        "For the working paper: Ibnat, N. (2026). Does money buy speed? Financial resources and sporting performance in Formula 1, 2010 to 2025 [Working paper]. F1 Moneyball. For the other studies, the data or the project: Ibnat, N. (2026). F1 Moneyball: An independent Formula 1 economics and finance research platform [Website]."),
    ],
  },
];

function FaqJsonLd() {
  const data = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: GROUPS.flatMap((g) => g.items).map((i) => ({
      "@type": "Question", name: i.q, acceptedAnswer: { "@type": "Answer", text: i.text },
    })),
  };
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}

export default function Faq() {
  return (
    <>
      <FaqJsonLd />
      <PageHeader eyebrow="FAQ" title="Questions and definitions"
        lede="Plain answers to the questions people ask most, and what the main terms mean." />
      <Section>
        <div className="grid lg:grid-cols-[15rem_minmax(0,1fr)] gap-10">
          <nav aria-label="FAQ sections" className="lg:sticky lg:top-6 self-start">
            <div className="label mb-3">Sections</div>
            <ul className="grid gap-2 font-mono text-sm">
              {GROUPS.map((g) => (
                <li key={g.id}><a className="hover:text-accent-fg" href={`#${g.id}`}>{g.title}</a></li>
              ))}
            </ul>
          </nav>
          <div className="min-w-0 grid gap-12">
            {GROUPS.map((g) => (
              <section key={g.id} id={g.id} aria-labelledby={`${g.id}-h`} className="scroll-mt-6">
                <h2 id={`${g.id}-h`} className="font-display font-semibold uppercase text-3xl text-head tracking-wide mb-4">{g.title}</h2>
                <div className="border-t border-line">
                  {g.items.map((i) => (
                    <details key={i.id} id={i.id} className="group border-b border-line">
                      <summary className="cursor-pointer list-none flex items-start justify-between gap-4 py-4 font-serif text-lg text-head hover:text-accent-fg">
                        <span>{i.q}</span>
                        <span aria-hidden className="font-mono text-race shrink-0 transition-transform group-open:rotate-45">+</span>
                      </summary>
                      <div className="prose-body pb-5 -mt-1">{i.a}</div>
                    </details>
                  ))}
                </div>
              </section>
            ))}
            <Callout title="Still have a question?">
              Ask on <a href={`${REPO}/issues`}>GitHub</a>, or read the <Link to="/methodology">Methodology</Link> page for the full details.
            </Callout>
          </div>
        </div>
      </Section>
    </>
  );
}
