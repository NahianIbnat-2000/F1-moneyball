import { Link, useParams } from "react-router-dom";
import ResearchArticle from "../components/article/ResearchArticle";
import { PageHeader } from "../components/Ui";
import { articleBySlug } from "../lib/articles";

export default function ArticlePage() {
  const { slug = "" } = useParams();
  const a = articleBySlug(slug);
  if (!a) return <PageHeader eyebrow="404" title="Article not found"><Link className="underline mt-4 inline-block" to="/research">All research</Link></PageHeader>;
  return <ResearchArticle a={a} />;
}
