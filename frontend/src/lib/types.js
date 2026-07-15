/**
 * JSDoc type mirrors of the backend's Pydantic schemas (app/models/schemas.py).
 * Kept in one file so every component references the same shape without
 * needing a TypeScript build step for the MVP.
 *
 * @typedef {Object} IssueBranch
 * @property {string} id
 * @property {string} title
 * @property {string} hypothesis
 * @property {"market_sizing"|"financial_analysis"|"sensitivity"|"qualitative"} analysis_type
 * @property {string[]} key_questions
 *
 * @typedef {Object} IssueTree
 * @property {string} root_question
 * @property {string} restated_question
 * @property {IssueBranch[]} branches
 * @property {string} created_at
 *
 * @typedef {Object} Evidence
 * @property {string} source
 * @property {string} snippet
 * @property {number} score
 * @property {Record<string, any>} metadata
 *
 * @typedef {Object} QuantResult
 * @property {string} method
 * @property {Record<string, any>} inputs
 * @property {Record<string, any>} outputs
 * @property {string} [narrative]
 *
 * @typedef {"pending"|"supported"|"partially_supported"|"refuted"|"inconclusive"} HypothesisStatus
 *
 * @typedef {Object} HypothesisFinding
 * @property {string} branch_id
 * @property {string} branch_title
 * @property {HypothesisStatus} status
 * @property {string} so_what
 * @property {Evidence[]} evidence
 * @property {QuantResult} [quant_result]
 * @property {number} confidence
 *
 * @typedef {Object} Recommendation
 * @property {string} headline
 * @property {string} executive_summary
 * @property {string[]} supporting_points
 * @property {string[]} risks_and_caveats
 * @property {number} confidence
 *
 * @typedef {Object} AnalysisResponse
 * @property {Object} request
 * @property {IssueTree} issue_tree
 * @property {HypothesisFinding[]} findings
 * @property {Recommendation} recommendation
 * @property {string} generated_at
 */

export {};
