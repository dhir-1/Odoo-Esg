import { useState, useEffect } from "react";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";
import { Badge } from "@/components/ecosphere/badge";
import { apiFetch } from "@/lib/api-client";
import { toast } from "sonner";
import { Settings, Plus, Save, Building, Tag, Sparkles } from "lucide-react";

interface Department {
  id: number;
  name: string;
  code: string;
  head_employee_id?: number;
  parent_department_id?: number;
  employee_count: number;
  status: string;
  head_employee_name?: string;
  parent_department_name?: string;
}

interface Category {
  id: number;
  name: string;
  type: "CSR_ACTIVITY" | "CHALLENGE";
  status: string;
}

interface ESGConfiguration {
  environmental_weight: number;
  social_weight: number;
  governance_weight: number;
  auto_emission_calculation_enabled: boolean;
  evidence_requirement_enabled: boolean;
  badge_auto_award_enabled: boolean;
  notify_on_compliance_issue: boolean;
}

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"esg" | "departments" | "categories">("esg");
  
  // Data lists
  const [departments, setDepartments] = useState<Department[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter Categories
  const [catTypeFilter, setCatTypeFilter] = useState<string>("All");

  // Form toggles
  const [showDeptForm, setShowDeptForm] = useState(false);
  const [showCatForm, setShowCatForm] = useState(false);

  // ESG Configuration states
  const [esgConfig, setEsgConfig] = useState<ESGConfiguration>({
    environmental_weight: 0.4,
    social_weight: 0.3,
    governance_weight: 0.3,
    auto_emission_calculation_enabled: true,
    evidence_requirement_enabled: true,
    badge_auto_award_enabled: true,
    notify_on_compliance_issue: true
  });

  // Department Form state
  const [deptForm, setDeptForm] = useState({
    name: "", code: "", head_employee_id: "", parent_department_id: "", status: "Active"
  });

  // Category Form state
  const [catForm, setCatForm] = useState({
    name: "", type: "CSR_ACTIVITY", status: "Active"
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [depts, cats, config] = await Promise.all([
        apiFetch<Department[]>("/departments/"),
        apiFetch<Category[]>("/categories/"),
        apiFetch<ESGConfiguration>("/settings/esg-configuration")
      ]);
      setDepartments(depts);
      setCategories(cats);
      setEsgConfig(config);
    } catch (err: any) {
      toast.error(err.message || "Failed to load settings configuration.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveESGConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Client-side weights validation sum to exactly 1.0
    const sum = Number(esgConfig.environmental_weight) + Number(esgConfig.social_weight) + Number(esgConfig.governance_weight);
    if (Math.abs(sum - 1.0) > 0.0001) {
      toast.error(`Validation Error: ESG Weights must equal exactly 1.0. Current sum is: ${sum}`);
      return;
    }

    try {
      // Save Weights and general toggles
      const newConfig = await apiFetch<ESGConfiguration>("/settings/esg-configuration", {
        method: "PATCH",
        body: JSON.stringify({
          environmental_weight: Number(esgConfig.environmental_weight),
          social_weight: Number(esgConfig.social_weight),
          governance_weight: Number(esgConfig.governance_weight),
          auto_emission_calculation_enabled: esgConfig.auto_emission_calculation_enabled,
          evidence_requirement_enabled: esgConfig.evidence_requirement_enabled,
          badge_auto_award_enabled: esgConfig.badge_auto_award_enabled,
          notify_on_compliance_issue: esgConfig.notify_on_compliance_issue
        })
      });
      setEsgConfig(newConfig);
      toast.success("ESG Configuration parameters saved successfully!");
    } catch (err: any) {
      toast.error(err.message || "Failed to save weights and toggles.");
    }
  };

  const handleCreateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    // Front-end circular check validation (cannot be its own parent)
    if (deptForm.parent_department_id && deptForm.parent_department_id === deptForm.code) {
      toast.error("Circular Dependency Error: A department cannot list itself as a parent.");
      return;
    }
    
    try {
      await apiFetch("/departments/", {
        method: "POST",
        body: JSON.stringify({
          name: deptForm.name,
          code: deptForm.code,
          head_employee_id: deptForm.head_employee_id ? Number(deptForm.head_employee_id) : undefined,
          parent_department_id: deptForm.parent_department_id ? Number(deptForm.parent_department_id) : undefined,
          status: deptForm.status
        })
      });
      toast.success("Department created successfully!");
      setShowDeptForm(false);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create department.");
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/categories/", {
        method: "POST",
        body: JSON.stringify(catForm)
      });
      toast.success("Initiative category created successfully!");
      setShowCatForm(false);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create category.");
    }
  };

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // Filter Categories by Type
  const filteredCategories = categories.filter(c => {
    if (catTypeFilter === "All") return true;
    return c.type === catTypeFilter;
  });

  return (
    <div className="mx-auto max-w-7xl font-sans text-foreground">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl flex items-center gap-2">
            <Settings className="h-7 w-7 text-primary" /> Settings & Console
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Configure ESG weight allocations, manage departmental structure tree, and customize scoring metrics.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border mb-6 overflow-x-auto">
        <button onClick={() => setActiveTab("esg")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "esg" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>ESG Configuration</button>
        <button onClick={() => setActiveTab("departments")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "departments" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Departments</button>
        <button onClick={() => setActiveTab("categories")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "categories" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Categories</button>
      </div>

      {activeTab === "esg" && (
        <form onSubmit={handleSaveESGConfig} className="space-y-6 max-w-3xl">
          <Card hover={false} className="p-6 border-l-4 border-l-primary">
            <h3 className="font-display text-lg font-bold mb-4 flex items-center gap-1.5">
              <Sparkles className="h-5 w-5 text-gold animate-pulse" /> ESG Index Weight Distributions
            </h3>
            <p className="text-xs text-muted-foreground mb-6 leading-relaxed">
              Weights represent the proportional impact of Environmental, Social, and Governance scores on the Overall ESG Index calculation. The sum of all three parameters must equal exactly 1.0 (100%).
            </p>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
              <div>
                <label className="block text-xs font-semibold uppercase text-accent-700 mb-1">Environmental Weight</label>
                <input type="number" min="0" max="1" step="0.05" required value={esgConfig.environmental_weight} onChange={(e) => setEsgConfig({ ...esgConfig, environmental_weight: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 font-body text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-secondary-700 mb-1">Social Weight</label>
                <input type="number" min="0" max="1" step="0.05" required value={esgConfig.social_weight} onChange={(e) => setEsgConfig({ ...esgConfig, social_weight: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 font-body text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-secondary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-primary-700 mb-1">Governance Weight</label>
                <input type="number" min="0" max="1" step="0.05" required value={esgConfig.governance_weight} onChange={(e) => setEsgConfig({ ...esgConfig, governance_weight: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 font-body text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
            </div>
            <div className="text-xs font-semibold text-muted-foreground mt-4 font-body">
              Current Weights Sum: {(Number(esgConfig.environmental_weight) + Number(esgConfig.social_weight) + Number(esgConfig.governance_weight)).toFixed(2)}
            </div>
          </Card>

          <Card hover={false} className="p-6 border-l-4 border-l-primary">
            <h3 className="font-display text-lg font-bold mb-6">Operational Toggles</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-border/60">
                <div>
                  <div className="text-sm font-semibold text-foreground">Auto Emission Calculation</div>
                  <div className="text-xs text-muted-foreground">Calculate emissions automatically using factor variables upon audit log ingestion.</div>
                </div>
                <input type="checkbox" checked={esgConfig.auto_emission_calculation_enabled} onChange={(e) => setEsgConfig({ ...esgConfig, auto_emission_calculation_enabled: e.target.checked })} className="h-5 w-5 rounded border-border text-primary focus:ring-primary" />
              </div>

              <div className="flex items-center justify-between py-2 border-b border-border/60">
                <div>
                  <div className="text-sm font-semibold text-foreground">Require CSR Evidence Proofs</div>
                  <div className="text-xs text-muted-foreground">Strictly enforce employees uploading attachments before managers can approve items.</div>
                </div>
                <input type="checkbox" checked={esgConfig.evidence_requirement_enabled} onChange={(e) => setEsgConfig({ ...esgConfig, evidence_requirement_enabled: e.target.checked })} className="h-5 w-5 rounded border-border text-primary focus:ring-primary" />
              </div>

              <div className="flex items-center justify-between py-2 border-b border-border/60">
                <div>
                  <div className="text-sm font-semibold text-foreground">Auto-Award Badges</div>
                  <div className="text-xs text-muted-foreground">Issue system milestones instantly once the points thresholds are resolved.</div>
                </div>
                <input type="checkbox" checked={esgConfig.badge_auto_award_enabled} onChange={(e) => setEsgConfig({ ...esgConfig, badge_auto_award_enabled: e.target.checked })} className="h-5 w-5 rounded border-border text-primary focus:ring-primary" />
              </div>

              <div className="flex items-center justify-between py-2 border-b border-border/60">
                <div>
                  <div className="text-sm font-semibold text-foreground">Compliance Alerts</div>
                  <div className="text-xs text-muted-foreground">Send email notifications automatically when compliance issues are reported.</div>
                </div>
                <input type="checkbox" checked={esgConfig.notify_on_compliance_issue} onChange={(e) => setEsgConfig({ ...esgConfig, notify_on_compliance_issue: e.target.checked })} className="h-5 w-5 rounded border-border text-primary focus:ring-primary" />
              </div>
            </div>
          </Card>

          <Button type="submit" variant="primary" className="w-full flex items-center gap-1">
            <Save className="h-4 w-4" /> Save Settings Configuration
          </Button>
        </form>
      )}

      {activeTab === "departments" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="font-display text-lg font-bold text-foreground flex items-center gap-1">
              <Building className="h-5 w-5 text-primary" /> Department Tree
            </h3>
            <Button variant="primary" size="sm" onClick={() => setShowDeptForm(!showDeptForm)}>
              <Plus className="h-4 w-4" /> {showDeptForm ? "Close Form" : "Add Department"}
            </Button>
          </div>

          {showDeptForm && (
            <Card hover={false} className="p-6 border-l-4 border-l-primary animate-in fade-in duration-200">
              <h4 className="font-display text-md font-bold mb-4">Add Department</h4>
              <form onSubmit={handleCreateDepartment} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Department Name</label>
                  <input type="text" required value={deptForm.name} onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Unique Code (e.g. IT, MK)</label>
                  <input type="text" required value={deptForm.code} onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Head Employee ID (Optional)</label>
                  <input type="number" placeholder="Employee Head ID" value={deptForm.head_employee_id} onChange={(e) => setDeptForm({ ...deptForm, head_employee_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Parent Department ID (Optional)</label>
                  <input type="number" placeholder="Parent ID for hierarchy" value={deptForm.parent_department_id} onChange={(e) => setDeptForm({ ...deptForm, parent_department_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
                </div>
                <div className="sm:col-span-2">
                  <Button type="submit" variant="primary" className="w-full">Create Department</Button>
                </div>
              </form>
            </Card>
          )}

          <Card hover={false} className="overflow-x-auto p-0">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Department Name</th>
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Code</th>
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Head</th>
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Parent Dept</th>
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs text-center">Employees</th>
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Status</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((d) => (
                  <tr key={d.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                    <td className="p-4 font-medium text-foreground">{d.name}</td>
                    <td className="p-4 font-body text-muted-foreground">{d.code}</td>
                    <td className="p-4 text-muted-foreground">{d.head_employee_name || "-"}</td>
                    <td className="p-4 text-muted-foreground">{d.parent_department_name || "-"}</td>
                    <td className="p-4 font-body font-semibold text-center">{d.employee_count}</td>
                    <td className="p-4">
                      <Badge variant={d.status === "Active" ? "accent" : "danger"}>{d.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {activeTab === "categories" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="font-display text-lg font-bold text-foreground flex items-center gap-1">
              <Tag className="h-5 w-5 text-primary" /> Master Categories
            </h3>
            <Button variant="primary" size="sm" onClick={() => setShowCatForm(!showCatForm)}>
              <Plus className="h-4 w-4" /> {showCatForm ? "Close Form" : "Add Category"}
            </Button>
          </div>

          {showCatForm && (
            <Card hover={false} className="p-6 border-l-4 border-l-primary animate-in fade-in duration-200">
              <h4 className="font-display text-md font-bold mb-4">Add Initiative Category</h4>
              <form onSubmit={handleCreateCategory} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Category Name</label>
                  <input type="text" required value={catForm.name} onChange={(e) => setCatForm({ ...catForm, name: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Pillar Type</label>
                  <select value={catForm.type} onChange={(e) => setCatForm({ ...catForm, type: e.target.value as any })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                    <option value="CSR_ACTIVITY">CSR Activity</option>
                    <option value="CHALLENGE">Challenge</option>
                  </select>
                </div>
                <div className="sm:col-span-2 font-body text-xs text-muted-foreground py-1">
                  Active categories will instantly become selectable in standard modules.
                </div>
                <div className="sm:col-span-2">
                  <Button type="submit" variant="primary" className="w-full">Create Category</Button>
                </div>
              </form>
            </Card>
          )}

          {/* Subfilter categories by Pillar Type */}
          <div className="flex gap-2 mb-4 overflow-x-auto py-1">
            {["All", "CSR_ACTIVITY", "CHALLENGE"].map((ct) => (
              <button key={ct} onClick={() => setCatTypeFilter(ct)} className={`px-3 py-1 text-xs font-semibold rounded-full border transition-all ${catTypeFilter === ct ? "bg-primary border-primary text-white" : "border-border text-muted-foreground hover:bg-muted"}`}>{ct.replace("_", " ")}</button>
            ))}
          </div>

          <Card hover={false} className="overflow-x-auto p-0">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Category Name</th>
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Type</th>
                  <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredCategories.map((c) => (
                  <tr key={c.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                    <td className="p-4 font-medium text-foreground">{c.name}</td>
                    <td className="p-4">
                      <Badge variant={c.type === "CSR_ACTIVITY" ? "secondary" : "gold"}>{c.type}</Badge>
                    </td>
                    <td className="p-4">
                      <Badge variant={c.status === "Active" ? "accent" : "danger"}>{c.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}
    </div>
  );
}
