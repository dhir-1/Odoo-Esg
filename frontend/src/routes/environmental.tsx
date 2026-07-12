import { useState, useEffect } from "react";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";
import { Badge } from "@/components/ecosphere/badge";
import { apiFetch } from "@/lib/api-client";
import { toast } from "sonner";
import { Leaf, Plus, Sparkles } from "lucide-react";

interface EmissionFactor {
  id: number;
  name: string;
  activity_type: string;
  unit: string;
  co2e_per_unit: number;
  source_reference: string;
  effective_from: string;
  effective_to?: string;
  status: string;
}

interface ProductProfile {
  id: number;
  product_name: string;
  sku?: string;
  category: string;
  emission_factor_id?: number;
  sustainability_score?: number;
  lifecycle_notes?: string;
  status: string;
}

interface CarbonTransaction {
  id: number;
  department_id: number;
  source_module: string;
  quantity: number;
  calculated_co2e: number;
  transaction_date: string;
  notes?: string;
}

interface EnvironmentalGoal {
  id: number;
  title: string;
  description: string;
  metric_type: string;
  target_value: number;
  current_value: number;
  unit: string;
  start_date: string;
  target_date: string;
  lifecycle_status: string;
  progress_status?: string;
}

interface Department {
  id: number;
  name: string;
}

interface Category {
  id: number;
  name: string;
}

export function EnvironmentalPage() {
  const [activeTab, setActiveTab] = useState<"factors" | "profiles" | "transactions" | "goals">("factors");
  const [factors, setFactors] = useState<EmissionFactor[]>([]);
  const [profiles, setProfiles] = useState<ProductProfile[]>([]);
  const [transactions, setTransactions] = useState<CarbonTransaction[]>([]);
  const [goals, setGoals] = useState<EnvironmentalGoal[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  // Form states
  const [showForm, setShowForm] = useState(false);
  const [factorForm, setFactorForm] = useState({
    name: "", activity_type: "Purchase", unit: "", co2e_per_unit: 0,
    source_reference: "", effective_from: new Date().toISOString().split("T")[0]
  });
  const [profileForm, setProfileForm] = useState({
    product_name: "", sku: "", category: "", sustainability_score: 50,
    lifecycle_notes: "", emission_factor_id: ""
  });
  const [txForm, setTxForm] = useState({
    department_id: "", emission_factor_id: "", quantity: 0,
    transaction_date: new Date().toISOString().split("T")[0], notes: "", simulate: false
  });
  const [goalForm, setGoalForm] = useState({
    title: "", description: "", metric_type: "CO2e Reduction", target_value: 0,
    current_value: 0, unit: "kg", start_date: new Date().toISOString().split("T")[0],
    target_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0]
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [facs, profs, txs, gls, depts, cats] = await Promise.all([
        apiFetch<EmissionFactor[]>("/emission-factors/"),
        apiFetch<ProductProfile[]>("/product-esg-profiles/"),
        apiFetch<CarbonTransaction[]>("/carbon-transactions/"),
        apiFetch<EnvironmentalGoal[]>("/environmental-goals/"),
        apiFetch<Department[]>("/departments/"),
        apiFetch<Category[]>("/categories/"),
      ]);
      setFactors(facs);
      setProfiles(profs);
      setTransactions(txs);
      setGoals(gls);
      setDepartments(depts);
      setCategories(cats);
    } catch (err: any) {
      toast.error(err.message || "Failed to load Environmental module data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateFactor = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/emission-factors/", {
        method: "POST",
        body: JSON.stringify(factorForm)
      });
      toast.success("Emission Factor created successfully!");
      setShowForm(false);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create emission factor.");
    }
  };

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const body = {
        ...profileForm,
        emission_factor_id: profileForm.emission_factor_id ? Number(profileForm.emission_factor_id) : undefined,
        sustainability_score: Number(profileForm.sustainability_score)
      };
      await apiFetch("/product-esg-profiles/", {
        method: "POST",
        body: JSON.stringify(body)
      });
      toast.success("Product ESG Profile created successfully!");
      setShowForm(false);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create product profile.");
    }
  };

  const handleCreateTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const path = txForm.simulate ? "/carbon-transactions/simulate" : "/carbon-transactions/";
      const body = txForm.simulate ? {
        department_id: Number(txForm.department_id),
        emission_factor_id: Number(txForm.emission_factor_id),
        quantity: Number(txForm.quantity),
        source_module: "Purchase",
        transaction_date: txForm.transaction_date,
        notes: txForm.notes
      } : {
        department_id: Number(txForm.department_id),
        emission_factor_id: Number(txForm.emission_factor_id),
        quantity: Number(txForm.quantity),
        calculated_co2e: Number(txForm.quantity) * 0.5, // Simple client fallback
        transaction_date: txForm.transaction_date,
        notes: txForm.notes
      };

      await apiFetch(path, {
        method: "POST",
        body: JSON.stringify(body)
      });
      toast.success(txForm.simulate ? "Simulated auto-calculated transaction logged!" : "Manual carbon transaction logged!");
      setShowForm(false);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to log transaction.");
    }
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (new Date(goalForm.target_date) < new Date(goalForm.start_date)) {
      toast.error("Target date must be after the start date.");
      return;
    }
    try {
      await apiFetch("/environmental-goals/", {
        method: "POST",
        body: JSON.stringify({
          ...goalForm,
          target_value: Number(goalForm.target_value),
          current_value: Number(goalForm.current_value)
        })
      });
      toast.success("Environmental Goal created successfully!");
      setShowForm(false);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create environmental goal.");
    }
  };

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl font-sans text-foreground">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl flex items-center gap-2">
            <Leaf className="h-7 w-7 text-accent" /> Environmental Management
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Track emission factors, operational footprints, and progress towards carbon targets.
          </p>
        </div>
        <Button variant="accent" onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> {showForm ? "Close Form" : "Add Record"}
        </Button>
      </div>

      {showForm && (
        <Card hover={false} className="mb-6 p-6 border-l-4 border-l-accent animate-in fade-in slide-in-from-top-4 duration-200">
          <h2 className="font-display text-lg font-bold mb-4">
            Create New {activeTab === "factors" ? "Emission Factor" : activeTab === "profiles" ? "Product Profile" : activeTab === "transactions" ? "Carbon Transaction" : "Environmental Goal"}
          </h2>
          
          {activeTab === "factors" && (
            <form onSubmit={handleCreateFactor} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Name</label>
                <input type="text" required value={factorForm.name} onChange={(e) => setFactorForm({ ...factorForm, name: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Activity Type</label>
                <select value={factorForm.activity_type} onChange={(e) => setFactorForm({ ...factorForm, activity_type: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent">
                  <option value="Purchase">Purchase</option>
                  <option value="Manufacturing">Manufacturing</option>
                  <option value="Expense">Expense</option>
                  <option value="Fleet">Fleet</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Unit</label>
                <input type="text" required placeholder="e.g. kWh, Litres" value={factorForm.unit} onChange={(e) => setFactorForm({ ...factorForm, unit: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">CO2e Per Unit (kg)</label>
                <input type="number" step="any" min="0" required value={factorForm.co2e_per_unit} onChange={(e) => setFactorForm({ ...factorForm, co2e_per_unit: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Source Reference</label>
                <input type="text" required value={factorForm.source_reference} onChange={(e) => setFactorForm({ ...factorForm, source_reference: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Effective From</label>
                <input type="date" required value={factorForm.effective_from} onChange={(e) => setFactorForm({ ...factorForm, effective_from: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" variant="accent" className="w-full">Create Emission Factor</Button>
              </div>
            </form>
          )}

          {activeTab === "profiles" && (
            <form onSubmit={handleCreateProfile} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Product Name</label>
                <input type="text" required value={profileForm.product_name} onChange={(e) => setProfileForm({ ...profileForm, product_name: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">SKU</label>
                <input type="text" value={profileForm.sku} onChange={(e) => setProfileForm({ ...profileForm, sku: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Category</label>
                <input type="text" required value={profileForm.category} onChange={(e) => setProfileForm({ ...profileForm, category: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Sustainability Score (0-100)</label>
                <input type="number" min="0" max="100" value={profileForm.sustainability_score} onChange={(e) => setProfileForm({ ...profileForm, sustainability_score: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Emission Factor Association</label>
                <select value={profileForm.emission_factor_id} onChange={(e) => setProfileForm({ ...profileForm, emission_factor_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent">
                  <option value="">No Association</option>
                  {factors.map((f) => <option key={f.id} value={f.id}>{f.name} ({f.unit})</option>)}
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Lifecycle Notes</label>
                <textarea rows={3} value={profileForm.lifecycle_notes} onChange={(e) => setProfileForm({ ...profileForm, lifecycle_notes: e.target.value })} className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" variant="accent" className="w-full">Create Product ESG Profile</Button>
              </div>
            </form>
          )}

          {activeTab === "transactions" && (
            <form onSubmit={handleCreateTransaction} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Target Department</label>
                <select required value={txForm.department_id} onChange={(e) => setTxForm({ ...txForm, department_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent">
                  <option value="">Select Department</option>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Emission Factor Source</label>
                <select required value={txForm.emission_factor_id} onChange={(e) => setTxForm({ ...txForm, emission_factor_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent">
                  <option value="">Select Factor</option>
                  {factors.map((f) => <option key={f.id} value={f.id}>{f.name} ({f.co2e_per_unit} kg CO2e)</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Quantity</label>
                <input type="number" min="0" step="any" required value={txForm.quantity} onChange={(e) => setTxForm({ ...txForm, quantity: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Transaction Date</label>
                <input type="date" required value={txForm.transaction_date} onChange={(e) => setTxForm({ ...txForm, transaction_date: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div className="sm:col-span-2 flex items-center gap-2 py-2">
                <input type="checkbox" id="simulate_calc" checked={txForm.simulate} onChange={(e) => setTxForm({ ...txForm, simulate: e.target.checked })} className="rounded border-border bg-background focus:ring-accent" />
                <label htmlFor="simulate_calc" className="text-sm font-medium text-foreground flex items-center gap-1">
                  <Sparkles className="h-4 w-4 text-gold" /> Auto-calculate CO2e using backend database engine
                </label>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Notes</label>
                <textarea rows={2} value={txForm.notes} onChange={(e) => setTxForm({ ...txForm, notes: e.target.value })} className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" variant="accent" className="w-full">Log Transaction</Button>
              </div>
            </form>
          )}

          {activeTab === "goals" && (
            <form onSubmit={handleCreateGoal} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Goal Title</label>
                <input type="text" required value={goalForm.title} onChange={(e) => setGoalForm({ ...goalForm, title: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Metric Type</label>
                <input type="text" required value={goalForm.metric_type} onChange={(e) => setGoalForm({ ...goalForm, metric_type: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Target Value</label>
                <input type="number" min="0" required value={goalForm.target_value} onChange={(e) => setGoalForm({ ...goalForm, target_value: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Current Value</label>
                <input type="number" min="0" required value={goalForm.current_value} onChange={(e) => setGoalForm({ ...goalForm, current_value: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Unit</label>
                <input type="text" required value={goalForm.unit} onChange={(e) => setGoalForm({ ...goalForm, unit: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Start Date</label>
                <input type="date" required value={goalForm.start_date} onChange={(e) => setGoalForm({ ...goalForm, start_date: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Target Date</label>
                <input type="date" required value={goalForm.target_date} onChange={(e) => setGoalForm({ ...goalForm, target_date: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Description</label>
                <textarea rows={2} required value={goalForm.description} onChange={(e) => setGoalForm({ ...goalForm, description: e.target.value })} className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent" />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" variant="accent" className="w-full">Create Goal</Button>
              </div>
            </form>
          )}
        </Card>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border mb-6 overflow-x-auto">
        <button onClick={() => { setActiveTab("factors"); setShowForm(false); }} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "factors" ? "border-accent text-accent" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Emission Factors</button>
        <button onClick={() => { setActiveTab("profiles"); setShowForm(false); }} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "profiles" ? "border-accent text-accent" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Product Profiles</button>
        <button onClick={() => { setActiveTab("transactions"); setShowForm(false); }} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "transactions" ? "border-accent text-accent" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Carbon Ledger</button>
        <button onClick={() => { setActiveTab("goals"); setShowForm(false); }} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "goals" ? "border-accent text-accent" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Environmental Goals</button>
      </div>

      {/* Lists */}
      <Card hover={false} className="overflow-x-auto p-0">
        {activeTab === "factors" && (
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Name</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Type</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">CO2e / Unit</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Reference</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Status</th>
              </tr>
            </thead>
            <tbody>
              {factors.map((f) => (
                <tr key={f.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                  <td className="p-4 font-medium text-foreground">{f.name}</td>
                  <td className="p-4 text-muted-foreground">{f.activity_type}</td>
                  <td className="p-4 font-body">{f.co2e_per_unit} kg / {f.unit}</td>
                  <td className="p-4 text-muted-foreground">{f.source_reference}</td>
                  <td className="p-4">
                    <Badge variant={f.status === "Active" ? "accent" : "danger"}>{f.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {activeTab === "profiles" && (
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Product</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">SKU</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Category</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Sustainability Score</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Status</th>
              </tr>
            </thead>
            <tbody>
              {profiles.map((p) => (
                <tr key={p.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                  <td className="p-4 font-medium text-foreground">{p.product_name}</td>
                  <td className="p-4 font-body text-muted-foreground">{p.sku || "-"}</td>
                  <td className="p-4 text-muted-foreground">{p.category}</td>
                  <td className="p-4 font-body">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-primary">{p.sustainability_score || 0}</span>
                      <div className="h-2 w-20 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-accent" style={{ width: `${p.sustainability_score || 0}%` }} />
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <Badge variant={p.status === "Active" ? "accent" : "danger"}>{p.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {activeTab === "transactions" && (
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Date</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Source</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Quantity</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Calculated CO2e</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Notes</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                  <td className="p-4 font-body">{tx.transaction_date}</td>
                  <td className="p-4 text-muted-foreground">{tx.source_module}</td>
                  <td className="p-4 font-body">{tx.quantity}</td>
                  <td className="p-4 font-body font-semibold text-danger">{tx.calculated_co2e} kg</td>
                  <td className="p-4 text-muted-foreground">{tx.notes || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {activeTab === "goals" && (
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Goal</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Progress</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Target Date</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Lifecycle Status</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Progress Status</th>
              </tr>
            </thead>
            <tbody>
              {goals.map((g) => {
                const percent = Math.min(100, Math.max(0, (g.current_value / g.target_value) * 100));
                return (
                  <tr key={g.id} className="border-b border-border hover:bg-muted/10 transition-colors">
                    <td className="p-4">
                      <div className="font-medium text-foreground">{g.title}</div>
                      <div className="text-xs text-muted-foreground">{g.description}</div>
                    </td>
                    <td className="p-4">
                      <div className="flex flex-col gap-1 w-40">
                        <div className="flex justify-between text-xs font-semibold">
                          <span>{g.current_value} / {g.target_value} {g.unit}</span>
                          <span>{percent.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-accent" style={{ width: `${percent}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="p-4 font-body">{g.target_date}</td>
                    <td className="p-4">
                      <Badge variant={g.lifecycle_status === "Active" ? "accent" : "info"}>{g.lifecycle_status}</Badge>
                    </td>
                    <td className="p-4">
                      <Badge variant={g.progress_status === "OnTrack" || g.progress_status === "Achieved" ? "secondary" : "warning"}>
                        {g.progress_status || "Pending"}
                      </Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
