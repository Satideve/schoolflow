// C:\coding_projects\dev\schoolflow\frontend\src\pages\FeePlanDetail.tsx
import React from "react";
import { useParams, Link } from "react-router-dom";
import {
  useFeePlan,
  useFeePlanComponents,
  useFeeComponents,
  useCreateFeePlanComponent,
  useDeleteFeePlanComponent,
  useUpdateFeePlanComponent,
} from "../api/queries";
import { formatMoney } from "../lib/utils";
import { useToast } from "../components/ui/use-toast";

const FeePlanDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const feePlanId = id ? Number(id) : undefined;

  const { data: plan, isLoading, isError } = useFeePlan(id ?? undefined);
  const {
    data: components = [],
    isLoading: compsLoading,
    isError: compsError,
  } = useFeePlanComponents(id ?? undefined);

  const { data: allFeeComponents = [], isLoading: feeCompsLoading } =
    useFeeComponents();

  const createPlanComponent = useCreateFeePlanComponent();
  const deletePlanComponent = useDeleteFeePlanComponent();
  const updatePlanComponent = useUpdateFeePlanComponent();
  const toast = useToast();

  const [selectedComponentId, setSelectedComponentId] =
    React.useState<string>("");
  const [amountInput, setAmountInput] = React.useState<string>("");

  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [editingAmount, setEditingAmount] = React.useState<string>("");

  if (!id || !feePlanId) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight">Fee Plan</h1>
        <p className="text-sm text-red-600">
          No fee plan ID provided in the URL.
        </p>
        <Link
          to="/fee-plans"
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to Fee Plans
        </Link>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight">Fee Plan</h1>
        <p className="text-sm text-muted-foreground">Loading fee plan...</p>
      </div>
    );
  }

  if (isError || !plan) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight">Fee Plan</h1>
        <p className="text-sm text-red-600">
          Failed to load fee plan (ID: {id}).
        </p>
        <Link
          to="/fee-plans"
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to Fee Plans
        </Link>
      </div>
    );
  }

  const totalAmount = components.reduce((sum, c) => {
    const amountNum = Number((c as any).amount ?? 0);
    return sum + (isNaN(amountNum) ? 0 : amountNum);
  }, 0);

  const handleAddComponent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedComponentId || !amountInput) {
      try {
        toast.push("Please select a component and enter an amount.");
      } catch {
        console.log("Please select a component and enter an amount.");
      }
      return;
    }

    const fee_component_id = Number(selectedComponentId);
    const amount = Number(amountInput);
    if (!fee_component_id || isNaN(amount) || amount <= 0) {
      try {
        toast.push("Invalid component or amount.");
      } catch {
        console.log("Invalid component or amount.");
      }
      return;
    }

    try {
      await createPlanComponent.mutateAsync({
        fee_plan_id: feePlanId,
        fee_component_id,
        amount,
      });
      setAmountInput("");
      setSelectedComponentId("");
      try {
        toast.push("Component added to plan.");
      } catch {
        console.log("Component added to plan.");
      }
    } catch (err) {
      console.error("create fee plan component failed", err);
      try {
        toast.push("Failed to add component to plan.");
      } catch {
        console.log("Failed to add component to plan.");
      }
    }
  };

  const handleDeleteComponent = async (componentId: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to remove this component from the plan?"
    );
    if (!confirmed) return;

    try {
      await deletePlanComponent.mutateAsync(componentId);
      try {
        toast.push("Component removed from plan.");
      } catch {
        console.log("Component removed from plan.");
      }
    } catch (err) {
      console.error("delete fee plan component failed", err);
      try {
        toast.push("Failed to remove component from plan.");
      } catch {
        console.log("Failed to remove component from plan.");
      }
    }
  };

  const startEditing = (componentId: number, currentAmount: number) => {
    setEditingId(componentId);
    setEditingAmount(String(currentAmount));
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditingAmount("");
  };

  const handleSaveEdit = async (componentId: number) => {
    const amount = Number(editingAmount);
    if (isNaN(amount) || amount <= 0) {
      try {
        toast.push("Invalid amount.");
      } catch {
        console.log("Invalid amount.");
      }
      return;
    }

    try {
      await updatePlanComponent.mutateAsync({
        id: componentId,
        amount,
      });
      setEditingId(null);
      setEditingAmount("");
      try {
        toast.push("Component amount updated.");
      } catch {
        console.log("Component amount updated.");
      }
    } catch (err) {
      console.error("update fee plan component failed", err);
      try {
        toast.push("Failed to update component amount.");
      } catch {
        console.log("Failed to update component amount.");
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Fee Plan: {plan.name}
          </h1>
          <p className="text-sm text-muted-foreground">
            ID: <span className="font-mono">{plan.id}</span>
          </p>
        </div>
        <Link
          to="/fee-plans"
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to Fee Plans
        </Link>
      </div>

      <div className="bg-white rounded shadow p-4 space-y-2 max-w-md">
        <h2 className="text-lg font-semibold mb-2">Plan Details</h2>
        <div className="text-sm">
          <div className="flex justify-between mb-1">
            <span className="text-slate-600">Name</span>
            <span className="font-medium">{plan.name}</span>
          </div>
          <div className="flex justify-between mb-1">
            <span className="text-slate-600">Academic Year</span>
            <span className="font-medium">{plan.academic_year}</span>
          </div>
          <div className="flex justify-between mb-1">
            <span className="text-slate-600">Frequency</span>
            <span className="font-medium capitalize">{plan.frequency}</span>
          </div>
        </div>
      </div>

      {/* Add Component Form */}
      <div className="bg-white rounded shadow p-4 space-y-3 max-w-xl">
        <h2 className="text-lg font-semibold">Add Component</h2>
        <form
          onSubmit={handleAddComponent}
          className="flex flex-col md:flex-row gap-3 items-stretch md:items-end"
        >
          <div className="flex-1">
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Fee Component
            </label>
            <select
              className="w-full border rounded px-3 py-2 text-sm"
              value={selectedComponentId}
              onChange={(e) => setSelectedComponentId(e.target.value)}
              disabled={feeCompsLoading}
            >
              <option value="">Select component...</option>
              {allFeeComponents.map((fc: any) => (
                <option key={fc.id} value={fc.id}>
                  {fc.name}
                </option>
              ))}
            </select>
          </div>

          <div className="w-full md:w-40">
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Amount
            </label>
            <input
              type="number"
              min="0"
              step="0.01"
              className="w-full border rounded px-3 py-2 text-sm"
              value={amountInput}
              onChange={(e) => setAmountInput(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={createPlanComponent.isPending || feeCompsLoading}
            className="inline-flex items-center justify-center px-4 py-2 rounded bg-blue-600 text-white text-sm disabled:opacity-60"
          >
            {createPlanComponent.isPending ? "Adding..." : "Add"}
          </button>
        </form>
        <p className="text-xs text-slate-500">
          Adding a component will automatically refresh the components list and
          totals below.
        </p>
      </div>

      <div className="bg-white rounded shadow p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Components</h2>
          <div className="text-sm text-slate-600">
            Total:{" "}
            <span className="font-semibold">
              {formatMoney ? formatMoney(totalAmount) : totalAmount}
            </span>
          </div>
        </div>

        {compsLoading ? (
          <div className="text-sm text-muted-foreground">
            Loading components...
          </div>
        ) : compsError ? (
          <div className="text-sm text-red-600">
            Failed to load plan components.
          </div>
        ) : components.length === 0 ? (
          <div className="text-sm text-slate-600">
            No components found for this fee plan.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">ID</th>
                  <th className="p-2 text-left">Component</th>
                  <th className="p-2 text-left">Description</th>
                  <th className="p-2 text-right">Amount</th>
                  <th className="p-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {components.map((c) => {
                  const amountNum = Number((c as any).amount ?? 0);
                  const compDef = (allFeeComponents as any[]).find(
                    (fc) => fc.id === c.fee_component_id
                  );
                  const compName =
                    compDef?.name ?? `Component #${c.fee_component_id}`;
                  const compDesc = compDef?.description ?? "";

                  const isEditing = editingId === c.id;

                  return (
                    <tr key={c.id} className="border-t">
                      <td className="p-2">{c.id}</td>
                      <td className="p-2">{compName}</td>
                      <td className="p-2 text-slate-600">
                        {compDesc || <span className="text-slate-400">—</span>}
                      </td>
                      <td className="p-2 text-right font-mono">
                        {isEditing ? (
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            className="w-24 border rounded px-2 py-1 text-right text-xs"
                            value={editingAmount}
                            onChange={(e) =>
                              setEditingAmount(e.target.value)
                            }
                          />
                        ) : formatMoney ? (
                          formatMoney(amountNum)
                        ) : (
                          amountNum
                        )}
                      </td>
                      <td className="p-2 text-right space-x-2">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => handleSaveEdit(c.id)}
                              disabled={updatePlanComponent.isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-green-600 text-white text-xs disabled:opacity-60"
                            >
                              {updatePlanComponent.isPending
                                ? "Saving..."
                                : "Save"}
                            </button>
                            <button
                              type="button"
                              onClick={cancelEditing}
                              disabled={updatePlanComponent.isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-slate-300 text-slate-800 text-xs disabled:opacity-60"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => startEditing(c.id, amountNum)}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-slate-200 text-slate-800 text-xs"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteComponent(c.id)}
                              disabled={deletePlanComponent.isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-red-600 text-white text-xs disabled:opacity-60"
                            >
                              {deletePlanComponent.isPending
                                ? "Removing..."
                                : "Delete"}
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default FeePlanDetail;
