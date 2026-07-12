import { useState, useEffect } from "react";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";
import { Badge } from "@/components/ecosphere/badge";
import { apiFetch } from "@/lib/api-client";
import { toast } from "sonner";
import { FileText, Download, CheckCircle, Sparkles, Filter, Leaf, Users, Shield, Award } from "lucide-react";

interface Department {
  id: number;
  name: string;
}

interface Challenge {
  id: number;
  title: string;
}

export function ReportsPage() {
  // Navigation Tabs
  const [activeTab, setActiveTab] = useState<"standard" | "custom">("standard");
  const [loading, setLoading] = useState(false);
  const [reportResult, setReportResult] = useState<any | null>(null);
  const [selectedReportType, setSelectedReportType] = useState<string | null>(null);

  // Filters for Custom Report Builder
  const [departments, setDepartments] = useState<Department[]>([]);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [customFilters, setCustomFilters] = useState({
    department_id: "",
    date_from: "",
    date_to: "",
    module: "",
    employee_id: "",
    challenge_id: "",
    esg_category: ""
  });

  const loadFilterOptions = async () => {
    try {
      const [depts, challs] = await Promise.all([
        apiFetch<Department[]>("/departments/"),
        apiFetch<Challenge[]>("/challenges/challenges/")
      ]);
      setDepartments(depts);
      setChallenges(challs);
    } catch {}
  };

  useEffect(() => {
    loadFilterOptions();
  }, []);

  const generateReport = async (type: "environmental" | "social" | "governance" | "esg-summary") => {
    setLoading(true);
    setSelectedReportType(type);
    try {
      const data = await apiFetch<any>(`/reports/${type}`);
      setReportResult(data);
      toast.success(`${type.toUpperCase()} report generated successfully!`);
    } catch (err: any) {
      toast.error(err.message || "Failed to generate report.");
      setReportResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRunCustomReport = async () => {
    setLoading(true);
    setSelectedReportType("custom");
    try {
      const payload = {
        department_id: customFilters.department_id ? Number(customFilters.department_id) : undefined,
        date_from: customFilters.date_from || undefined,
        date_to: customFilters.date_to || undefined,
        module: customFilters.module || undefined,
        employee_id: customFilters.employee_id ? Number(customFilters.employee_id) : undefined,
        challenge_id: customFilters.challenge_id ? Number(customFilters.challenge_id) : undefined,
        esg_category: customFilters.esg_category || undefined,
        export_format: "json"
      };

      const data = await apiFetch<any>("/reports/custom", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setReportResult(data);
      toast.success("Custom query executed successfully!");
    } catch (err: any) {
      toast.error(err.message || "Failed to run custom query.");
      setReportResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: "csv" | "xlsx" | "pdf") => {
    setLoading(true);
    try {
      const payload = {
        department_id: customFilters.department_id ? Number(customFilters.department_id) : undefined,
        date_from: customFilters.date_from || undefined,
        date_to: customFilters.date_to || undefined,
        module: customFilters.module || undefined,
        employee_id: customFilters.employee_id ? Number(customFilters.employee_id) : undefined,
        challenge_id: customFilters.challenge_id ? Number(customFilters.challenge_id) : undefined,
        esg_category: customFilters.esg_category || undefined,
        export_format: format
      };

      const blob = await apiFetch<Blob>("/reports/custom", {
        method: "POST",
        body: JSON.stringify(payload),
        headers: {
          "Accept": format === "pdf" ? "application/pdf" : format === "xlsx" ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" : "text/csv"
        }
      });

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `custom_esg_report.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Exported successfully as ${format.toUpperCase()}!`);
    } catch (err: any) {
      toast.error(err.message || "Failed to export report.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl font-sans text-foreground">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl flex items-center gap-2">
            <FileText className="h-7 w-7 text-primary" /> Reports & Analytics
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Export unified ESG compliance parameters, social impact hours, and score distributions.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border mb-6 overflow-x-auto">
        <button onClick={() => { setActiveTab("standard"); setReportResult(null); setSelectedReportType(null); }} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "standard" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Standard Reports</button>
        <button onClick={() => { setActiveTab("custom"); setReportResult(null); setSelectedReportType(null); }} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "custom" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Custom Report Builder</button>
      </div>

      {activeTab === "standard" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card accent="accent" className="flex flex-col justify-between p-6">
              <div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 text-accent mb-4">
                  <Leaf className="h-5 w-5" />
                </div>
                <h3 className="font-display text-lg font-bold text-foreground">Environmental Report</h3>
                <p className="text-xs text-muted-foreground mt-1">Total CO2e footprint, goals tracker progress, and vendor breakdown analysis.</p>
              </div>
              <Button variant="accent" size="sm" className="mt-6 w-full" onClick={() => generateReport("environmental")}>Generate Report</Button>
            </Card>

            <Card accent="secondary" className="flex flex-col justify-between p-6">
              <div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary/10 text-secondary mb-4">
                  <Users className="h-5 w-5" />
                </div>
                <h3 className="font-display text-lg font-bold text-foreground">Social Impact Report</h3>
                <p className="text-xs text-muted-foreground mt-1">Approved CSR volunteer statistics, diversity metric segments, and training completion.</p>
              </div>
              <Button variant="secondary" size="sm" className="mt-6 w-full" onClick={() => generateReport("social")}>Generate Report</Button>
            </Card>

            <Card accent="primary" className="flex flex-col justify-between p-6">
              <div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary mb-4">
                  <Shield className="h-5 w-5" />
                </div>
                <h3 className="font-display text-lg font-bold text-foreground">Governance Report</h3>
                <p className="text-xs text-muted-foreground mt-1">Policy acknowledgement rates, audit logs, and compliance issues severity.</p>
              </div>
              <Button variant="primary" size="sm" className="mt-6 w-full" onClick={() => generateReport("governance")}>Generate Report</Button>
            </Card>

            <Card accent="gold" className="flex flex-col justify-between p-6">
              <div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gold/10 text-gold mb-4">
                  <Award className="h-5 w-5" />
                </div>
                <h3 className="font-display text-lg font-bold text-foreground">ESG Summary Overview</h3>
                <p className="text-xs text-muted-foreground mt-1">Unified executive overview containing all 4 score indices and department rankings.</p>
              </div>
              <Button variant="gold" size="sm" className="mt-6 w-full" onClick={() => generateReport("esg-summary")}>Generate Report</Button>
            </Card>
          </div>
        </div>
      )}

      {activeTab === "custom" && (
        <Card hover={false} className="p-6 border-l-4 border-l-primary mb-6">
          <h3 className="font-display text-lg font-bold mb-4 flex items-center gap-2">
            <Filter className="h-5 w-5 text-primary" /> Filter Options
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Department</label>
              <select value={customFilters.department_id} onChange={(e) => setCustomFilters({ ...customFilters, department_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                <option value="">All Departments</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Date From</label>
              <input type="date" value={customFilters.date_from} onChange={(e) => setCustomFilters({ ...customFilters, date_from: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Date To</label>
              <input type="date" value={customFilters.date_to} onChange={(e) => setCustomFilters({ ...customFilters, date_to: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Pillar Module</label>
              <select value={customFilters.module} onChange={(e) => setCustomFilters({ ...customFilters, module: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                <option value="">All Modules</option>
                <option value="Environmental">Environmental</option>
                <option value="Social">Social</option>
                <option value="Governance">Governance</option>
                <option value="Gamification">Gamification</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Employee ID</label>
              <input type="number" placeholder="Filter by Employee ID" value={customFilters.employee_id} onChange={(e) => setCustomFilters({ ...customFilters, employee_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Challenge</label>
              <select value={customFilters.challenge_id} onChange={(e) => setCustomFilters({ ...customFilters, challenge_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                <option value="">All Challenges</option>
                {challenges.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
              </select>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 mt-6 border-t border-border pt-4 justify-between">
            <Button variant="primary" onClick={handleRunCustomReport}>Run Report Builder</Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => handleExport("csv")} className="flex items-center gap-1">
                <Download className="h-4 w-4" /> CSV
              </Button>
              <Button variant="outline" onClick={() => handleExport("xlsx")} className="flex items-center gap-1">
                <Download className="h-4 w-4" /> XLSX
              </Button>
              <Button variant="outline" onClick={() => handleExport("pdf")} className="flex items-center gap-1">
                <Download className="h-4 w-4" /> PDF
              </Button>
            </div>
          </div>
        </Card>
      )}

      {loading && (
        <div className="flex h-40 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      )}

      {!loading && reportResult && (
        <Card hover={false} className="mt-6 p-6 border-l-4 border-l-primary animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between mb-4 border-b border-border pb-3">
            <h2 className="font-display text-lg font-bold text-foreground">
              Report Results: {selectedReportType?.toUpperCase()}
            </h2>
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <CheckCircle className="h-4 w-4 text-accent" /> Compiled successfully
            </span>
          </div>

          {selectedReportType === "environmental" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Card hover={false} className="p-4 bg-muted/20">
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Total Emissions Carbon Footprint</div>
                  <div className="font-body text-2xl font-bold text-danger mt-1">{reportResult.total_emissions_co2e} kg CO2e</div>
                </Card>
                <Card hover={false} className="p-4 bg-muted/20">
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Active Carbon Product Profiles</div>
                  <div className="font-body text-2xl font-bold text-foreground mt-1">{reportResult.product_profiles?.length || 0} Products</div>
                </Card>
              </div>

              {reportResult.goals && (
                <div>
                  <h4 className="font-display font-semibold mb-2">Target goal indicators</h4>
                  <ul className="space-y-2">
                    {reportResult.goals.map((g: any, i: number) => (
                      <li key={i} className="flex justify-between text-sm py-1.5 border-b border-border/40">
                        <span>{g.title || `Goal #${g.id}`}</span>
                        <span className="font-semibold text-accent">{g.progress_status || "Active"}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {selectedReportType === "social" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Card hover={false} className="p-4 bg-muted/20">
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Approved CSR Program Participations</div>
                  <div className="font-body text-2xl font-bold text-secondary mt-1">{reportResult.csr_stats?.total_approved_participations || 0} Participations</div>
                </Card>
                <Card hover={false} className="p-4 bg-muted/20">
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Volunteer CSR Impact Hours</div>
                  <div className="font-body text-2xl font-bold text-foreground mt-1">{reportResult.csr_stats?.total_csr_hours || 0} Hours</div>
                </Card>
              </div>

              {reportResult.training_completion_rate && (
                <div>
                  <h4 className="font-display font-semibold mb-2">Training Course Completion Indices</h4>
                  <ul className="space-y-2">
                    {Object.entries(reportResult.training_completion_rate).map(([course, rate]: any) => (
                      <li key={course} className="flex justify-between text-sm py-1.5 border-b border-border/40">
                        <span>{course}</span>
                        <span className="font-body font-semibold text-secondary">{rate}%</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {selectedReportType === "governance" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Card hover={false} className="p-4 bg-muted/20">
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Open Compliance Concerns</div>
                  <div className="font-body text-2xl font-bold text-danger mt-1">
                    {reportResult.compliance_summary?.open_issues || 0} Issues
                  </div>
                </Card>
                <Card hover={false} className="p-4 bg-muted/20">
                  <div className="text-xs font-semibold text-muted-foreground uppercase">Compliance Audits Checked</div>
                  <div className="font-body text-2xl font-bold text-foreground mt-1">
                    {reportResult.audits?.length || 0} Audits
                  </div>
                </Card>
              </div>

              {reportResult.policies && (
                <div>
                  <h4 className="font-display font-semibold mb-2">ESG Policies Acknowledgements</h4>
                  <ul className="space-y-2">
                    {reportResult.policies.map((p: any) => (
                      <li key={p.id} className="flex justify-between text-sm py-1.5 border-b border-border/40">
                        <span>{p.title} (v{p.version})</span>
                        <span className="font-body font-semibold text-primary">{p.acknowledgement_rate || 0}% acknowledged</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {selectedReportType === "esg-summary" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <Card hover={false} className="p-3 bg-muted/10">
                  <div className="text-xs font-semibold text-muted-foreground">Org Total Index</div>
                  <div className="font-body text-xl font-bold text-primary">{reportResult.org_total_score || 0}</div>
                </Card>
                <Card hover={false} className="p-3 bg-muted/10">
                  <div className="text-xs font-semibold text-muted-foreground">Environmental Avg</div>
                  <div className="font-body text-xl font-bold text-accent">{reportResult.org_environmental_avg || 0}</div>
                </Card>
                <Card hover={false} className="p-3 bg-muted/10">
                  <div className="text-xs font-semibold text-muted-foreground">Social Avg</div>
                  <div className="font-body text-xl font-bold text-secondary">{reportResult.org_social_avg || 0}</div>
                </Card>
                <Card hover={false} className="p-3 bg-muted/10">
                  <div className="text-xs font-semibold text-muted-foreground">Governance Avg</div>
                  <div className="font-body text-xl font-bold text-primary">{reportResult.org_governance_avg || 0}</div>
                </Card>
              </div>

              {reportResult.department_comparison && (
                <div>
                  <h4 className="font-display font-semibold mb-2">Departmental score matrix comparison</h4>
                  <div className="overflow-x-auto border border-border rounded-lg">
                    <table className="w-full text-left text-sm border-collapse">
                      <thead>
                        <tr className="bg-muted/40 border-b border-border">
                          <th className="p-3 font-semibold uppercase text-xs">Department</th>
                          <th className="p-3 font-semibold uppercase text-xs text-center">Environmental</th>
                          <th className="p-3 font-semibold uppercase text-xs text-center">Social</th>
                          <th className="p-3 font-semibold uppercase text-xs text-center">Governance</th>
                          <th className="p-3 font-semibold uppercase text-xs text-right">Total Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportResult.department_comparison.map((dept: any, index: number) => (
                          <tr key={index} className="border-b border-border/60 hover:bg-muted/10">
                            <td className="p-3 font-medium text-foreground">{dept.department_name}</td>
                            <td className="p-3 font-body text-center text-accent">{dept.environmental_score}</td>
                            <td className="p-3 font-body text-center text-secondary">{dept.social_score}</td>
                            <td className="p-3 font-body text-center text-primary">{dept.governance_score}</td>
                            <td className="p-3 font-body font-bold text-right text-primary">{dept.total_score}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {selectedReportType === "custom" && (
            <div className="space-y-4">
              <h4 className="font-display font-semibold mb-2">Raw JSON preview logs</h4>
              <pre className="p-4 bg-muted/60 text-xs text-foreground overflow-x-auto rounded-lg max-h-96 border border-border/80 font-mono">
                {JSON.stringify(reportResult, null, 2)}
              </pre>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
