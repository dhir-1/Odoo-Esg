import { useState, useEffect } from "react";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";
import { Badge } from "@/components/ecosphere/badge";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";
import { toast } from "sonner";
import { Shield, Plus, CheckCircle, AlertTriangle, FileText, User } from "lucide-react";
import { samplePolicies, sampleAudits, sampleComplianceIssues } from "@/lib/dashboard-mock-data";

interface ESGPolicy {
  id: number;
  title: string;
  description: string;
  category: string;
  version: string;
  document_url?: string;
  effective_date: string;
  requires_acknowledgement: boolean;
  status: string;
  acknowledgement_rate?: number;
}

interface Audit {
  id: number;
  title: string;
  department_id?: number;
  auditor_id?: number;
  audit_date: string;
  scope: string;
  findings_summary?: string;
  status: string;
  overall_rating?: number;
}

interface ComplianceIssue {
  id: number;
  audit_id?: number;
  description: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  status: "Open" | "In_Progress" | "Resolved" | "Closed";
  due_date: string;
  owner_id: number;
  owner_name?: string;
}

interface Employee {
  id: number;
  full_name: string;
}

export function GovernancePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"policies" | "audits" | "compliance">("policies");
  const [policies, setPolicies] = useState<ESGPolicy[]>([]);
  const [audits, setAudits] = useState<Audit[]>([]);
  const [issues, setIssues] = useState<ComplianceIssue[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Track local acknowledgements in session state
  const [localAcks, setLocalAcks] = useState<Record<number, boolean>>({});

  // Form states
  const [showForm, setShowForm] = useState(false);
  const [policyForm, setPolicyForm] = useState({
    title: "", description: "", category: "Environmental", version: "1.0",
    document_url: "", effective_date: new Date().toISOString().split("T")[0], requires_acknowledgement: true
  });
  const [auditForm, setAuditForm] = useState({
    title: "", department_id: "", auditor_id: "",
    audit_date: new Date().toISOString().split("T")[0], scope: "", findings_summary: "", overall_rating: 100
  });
  const [issueForm, setIssueForm] = useState({
    audit_id: "", description: "", severity: "Medium",
    due_date: new Date(Date.now() + 15 * 86400000).toISOString().split("T")[0], owner_id: ""
  });

  const loadData = async ({ silent = false }: { silent?: boolean } = {}) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const [pols, auds, iss, emps] = await Promise.all([
        apiFetch<ESGPolicy[]>("/governance/policies/"),
        apiFetch<Audit[]>("/governance/audits/"),
        apiFetch<ComplianceIssue[]>("/governance/compliance-issues/"),
        apiFetch<Employee[]>("/employees/", { params: { limit: 100, status: "Active" } })
      ]);
      setPolicies(pols);
      setAudits(auds);
      setIssues(iss);
      setEmployees(emps);
    } catch (err: any) {
      if (policies.length === 0) setPolicies(samplePolicies as ESGPolicy[]);
      if (audits.length === 0) setAudits(sampleAudits as Audit[]);
      if (issues.length === 0) setIssues(sampleComplianceIssues as ComplianceIssue[]);
      toast.error(err.message || "Failed to load Governance module data.");
    } finally {
      if (silent) setRefreshing(false);
      else setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/governance/policies/", {
        method: "POST",
        body: JSON.stringify(policyForm)
      });
      toast.success("ESG Policy created successfully in Draft mode!");
      setShowForm(false);
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to create policy.");
    }
  };

  const handleCreateAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/governance/audits/", {
        method: "POST",
        body: JSON.stringify({
          ...auditForm,
          department_id: auditForm.department_id ? Number(auditForm.department_id) : undefined,
          auditor_id: auditForm.auditor_id ? Number(auditForm.auditor_id) : undefined,
          overall_rating: Number(auditForm.overall_rating)
        })
      });
      toast.success("Audit entry scheduled successfully!");
      setShowForm(false);
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to create audit record.");
    }
  };

  const handleCreateIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!issueForm.owner_id || !issueForm.due_date) {
      toast.error("Owner and Due Date are strictly required fields.");
      return;
    }
    try {
      await apiFetch("/governance/compliance-issues/", {
        method: "POST",
        body: JSON.stringify({
          ...issueForm,
          audit_id: issueForm.audit_id ? Number(issueForm.audit_id) : undefined,
          owner_id: Number(issueForm.owner_id)
        })
      });
      toast.success("Compliance issue logged and assigned to owner!");
      setShowForm(false);
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to log compliance issue.");
    }
  };

  const handleAcknowledgePolicy = async (id: number) => {
    try {
      await apiFetch(`/governance/policies/${id}/acknowledge`, { method: "POST" });
      toast.success("Policy acknowledged successfully!");
      setLocalAcks(prev => ({ ...prev, [id]: true }));
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to acknowledge policy.");
    }
  };

  const visiblePolicies = policies.length === 0 ? (samplePolicies as ESGPolicy[]) : policies;
  const visibleAudits = audits.length === 0 ? (sampleAudits as Audit[]) : audits;
  const visibleIssues = issues.length === 0 ? (sampleComplianceIssues as ComplianceIssue[]) : issues;

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl font-sans text-foreground">
      {refreshing && (
        <div className="fixed bottom-4 right-4 z-40 rounded-full border border-border bg-card px-4 py-2 text-sm shadow-card">
          Refreshing data...
        </div>
      )}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl flex items-center gap-2">
            <Shield className="h-7 w-7 text-primary" /> Governance & Compliance
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Review ESG policies, track compliance audits, and manage corrective actions.
          </p>
        </div>
        {user?.role === "Admin" && (
          <Button variant="primary" onClick={() => setShowForm(!showForm)}>
            <Plus className="h-4 w-4" /> {showForm ? "Close Form" : `Create ${activeTab === "policies" ? "Policy" : activeTab === "audits" ? "Audit" : "Compliance Issue"}`}
          </Button>
        )}
      </div>

      {showForm && (
        <Card hover={false} className="mb-6 p-6 border-l-4 border-l-primary animate-in fade-in slide-in-from-top-4 duration-200">
          <h2 className="font-display text-lg font-bold mb-4">
            Create New {activeTab === "policies" ? "Policy" : activeTab === "audits" ? "Audit" : "Compliance Issue"}
          </h2>

          {activeTab === "policies" && (
            <form onSubmit={handleCreatePolicy} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Title</label>
                <input type="text" required value={policyForm.title} onChange={(e) => setPolicyForm({ ...policyForm, title: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Category</label>
                <select value={policyForm.category} onChange={(e) => setPolicyForm({ ...policyForm, category: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                  <option value="Environmental">Environmental</option>
                  <option value="Social">Social</option>
                  <option value="Governance">Governance</option>
                  <option value="General">General</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Version</label>
                <input type="text" required value={policyForm.version} onChange={(e) => setPolicyForm({ ...policyForm, version: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Effective Date</label>
                <input type="date" required value={policyForm.effective_date} onChange={(e) => setPolicyForm({ ...policyForm, effective_date: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Document URL (Optional)</label>
                <input type="url" placeholder="https://example.com/policy.pdf" value={policyForm.document_url} onChange={(e) => setPolicyForm({ ...policyForm, document_url: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Description</label>
                <textarea rows={3} required value={policyForm.description} onChange={(e) => setPolicyForm({ ...policyForm, description: e.target.value })} className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" variant="primary" className="w-full">Create ESG Policy</Button>
              </div>
            </form>
          )}

          {activeTab === "audits" && (
            <form onSubmit={handleCreateAudit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Audit Title</label>
                <input type="text" required value={auditForm.title} onChange={(e) => setAuditForm({ ...auditForm, title: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Audit Date</label>
                <input type="date" required value={auditForm.audit_date} onChange={(e) => setAuditForm({ ...auditForm, audit_date: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Department ID</label>
                <input type="number" placeholder="Empty for company-wide" value={auditForm.department_id} onChange={(e) => setAuditForm({ ...auditForm, department_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Auditor Employee ID</label>
                <input type="number" value={auditForm.auditor_id} onChange={(e) => setAuditForm({ ...auditForm, auditor_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Scope description</label>
                <input type="text" required value={auditForm.scope} onChange={(e) => setAuditForm({ ...auditForm, scope: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Findings Summary</label>
                <textarea rows={2} value={auditForm.findings_summary} onChange={(e) => setAuditForm({ ...auditForm, findings_summary: e.target.value })} className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" variant="primary" className="w-full">Create Audit</Button>
              </div>
            </form>
          )}

          {activeTab === "compliance" && (
            <form onSubmit={handleCreateIssue} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Associated Audit ID (Optional)</label>
                <input type="number" value={issueForm.audit_id} onChange={(e) => setIssueForm({ ...issueForm, audit_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Severity</label>
                <select value={issueForm.severity} onChange={(e) => setIssueForm({ ...issueForm, severity: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Due Date <span className="text-danger font-semibold">*</span></label>
                <input type="date" required value={issueForm.due_date} onChange={(e) => setIssueForm({ ...issueForm, due_date: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Owner Employee ID <span className="text-danger font-semibold">*</span></label>
                <select required value={issueForm.owner_id} onChange={(e) => setIssueForm({ ...issueForm, owner_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                  <option value="">Select Owner</option>
                  {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.full_name} (ID: {emp.id})</option>)}
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Description <span className="text-danger font-semibold">*</span></label>
                <textarea rows={3} required value={issueForm.description} onChange={(e) => setIssueForm({ ...issueForm, description: e.target.value })} className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" variant="primary" className="w-full">Raise Compliance Issue</Button>
              </div>
            </form>
          )}
        </Card>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border mb-6 overflow-x-auto">
        <button onClick={() => setActiveTab("policies")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "policies" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>ESG Policies</button>
        <button onClick={() => setActiveTab("audits")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "audits" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Audits</button>
        <button onClick={() => setActiveTab("compliance")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "compliance" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Compliance Issues</button>
      </div>

      <Card hover={false} className="overflow-x-auto p-0">
        {activeTab === "policies" && (
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Policy</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Category</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Version</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Effective Date</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Status</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs text-right">Acknowledgement</th>
              </tr>
            </thead>
            <tbody>
              {visiblePolicies.map((p) => {
                const isAcknowledged = localAcks[p.id];
                return (
                  <tr key={p.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                    <td className="p-4">
                      <div className="font-medium text-foreground">{p.title}</div>
                      <div className="text-xs text-muted-foreground">{p.description}</div>
                      {p.document_url && (
                        <a href={p.document_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline flex items-center gap-1 mt-1">
                          <FileText className="h-3.5 w-3.5" /> View document PDF
                        </a>
                      )}
                    </td>
                    <td className="p-4 text-muted-foreground">{p.category}</td>
                    <td className="p-4 font-body">{p.version}</td>
                    <td className="p-4 font-body">{p.effective_date}</td>
                    <td className="p-4">
                      <Badge variant={p.status === "Active" ? "accent" : p.status === "Draft" ? "info" : "danger"}>
                        {p.status}
                      </Badge>
                    </td>
                    <td className="p-4 text-right">
                      {p.requires_acknowledgement ? (
                        isAcknowledged ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-accent py-1 px-2.5 bg-accent-50 rounded-full">
                            <CheckCircle className="h-4 w-4" /> Acknowledged
                          </span>
                        ) : (
                          <Button variant="primary" size="sm" onClick={() => handleAcknowledgePolicy(p.id)}>
                            Acknowledge
                          </Button>
                        )
                      ) : (
                        <span className="text-xs text-muted-foreground italic">Not Required</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {activeTab === "audits" && (
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Audit Title</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Date</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Auditor ID</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Scope</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Findings Summary</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Status</th>
              </tr>
            </thead>
            <tbody>
              {visibleAudits.map((a) => (
                <tr key={a.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                  <td className="p-4 font-medium text-foreground">{a.title}</td>
                  <td className="p-4 font-body">{a.audit_date}</td>
                  <td className="p-4 font-body text-muted-foreground">{a.auditor_id || "-"}</td>
                  <td className="p-4 text-muted-foreground">{a.scope}</td>
                  <td className="p-4 text-muted-foreground">{a.findings_summary || "-"}</td>
                  <td className="p-4">
                    <Badge variant={a.status === "Completed" ? "accent" : a.status === "Scheduled" ? "info" : "warning"}>
                      {a.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {activeTab === "compliance" && (
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Description</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Severity</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Owner</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Due Date</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Status</th>
              </tr>
            </thead>
            <tbody>
              {visibleIssues.map((i) => (
                <tr key={i.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                  <td className="p-4 font-medium text-foreground">{i.description}</td>
                  <td className="p-4">
                    <Badge variant={i.severity === "Critical" || i.severity === "High" ? "danger" : i.severity === "Medium" ? "warning" : "info"}>
                      {i.severity}
                    </Badge>
                  </td>
                  <td className="p-4 text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <User className="h-3.5 w-3.5 text-muted-foreground" /> Employee {i.owner_id}
                    </span>
                  </td>
                  <td className="p-4 font-body text-danger font-semibold">{i.due_date}</td>
                  <td className="p-4">
                    <Badge variant={i.status === "Resolved" || i.status === "Closed" ? "accent" : "warning"}>
                      {i.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
