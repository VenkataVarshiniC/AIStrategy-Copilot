import Shell from "./components/layout/Shell.jsx";
import QuestionForm from "./components/question/QuestionForm.jsx";
import IngestPanel from "./components/ingestion/IngestPanel.jsx";
import IssueTreeView from "./components/issuetree/IssueTreeView.jsx";
import RecommendationSummary from "./components/recommendation/RecommendationSummary.jsx";
import LoadingState from "./components/common/LoadingState.jsx";
import EmptyState from "./components/common/EmptyState.jsx";
import ErrorBanner from "./components/common/ErrorBanner.jsx";
import { useAnalysis } from "./hooks/useAnalysis.js";

export default function App() {
  const { status, result, error, submit, reset } = useAnalysis();

  return (
    <Shell
      sidebar={
        <>
          <QuestionForm onSubmit={submit} disabled={status === "loading"} />
          <IngestPanel />
        </>
      }
    >
      {status === "idle" && <EmptyState />}
      {status === "loading" && <LoadingState />}
      {status === "error" && <ErrorBanner message={error} onRetry={reset} />}
      {status === "success" && result && (
        <>
          <RecommendationSummary recommendation={result.recommendation} />
          <IssueTreeView issueTree={result.issue_tree} findings={result.findings} />
        </>
      )}
    </Shell>
  );
}
