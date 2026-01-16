
# Codebase structure (commit 32b6666)

Layout captured from commit 32b6666 on main prior to the doc-organisation merge. All entries are relative to the repo root.

## High-level layout
- Architecture.md: top-level overview document
- Backend/: Python backend, graph orchestration, MCP config, Text2SQL, prompts, utilities, and renderer assets
- Docs/: legacy documentation (largely James' notes)
- Frontend/: Nuxt/Vue front-end app, multi-agent orchestrators, and a lightweight Python service for the UI
- Local Agent/: Speckle Connector C# solution with CI configs and source code
- Services/: bundled Speckle server monorepo (apps, packages, deployment assets, tests)
- requirements/: consolidated dependency lockfiles and setup guides
- sandbox/: experimental MCP agents, IFC utilities, old agent snapshots, and demos

## Full tree (files and folders)
```
.
|-- Backend/
|   |-- config/
|   |   |-- __init__.py
|   |   |-- llm_instances.py
|   |   |-- logging_config.py
|   |   `-- settings.py
|   |-- graph/
|   |   |-- subgraphs/
|   |   |   |-- __init__.py
|   |   |   |-- build_model_gen_subgraph.py
|   |   |   |-- db_retrieval_subgraph.py
|   |   |   |-- desktop_agent_subgraph.py
|   |   |   `-- webcalcs_subgraph.py
|   |   |-- __init__.py
|   |   |-- builder.py
|   |   `-- checkpointer.py
|   |-- helpers/
|   |   |-- __init__.py
|   |   |-- enhanced_logger.py
|   |   |-- feedback_logger.py
|   |   |-- instructions.py
|   |   `-- supabase_logger.py
|   |-- models/
|   |   |-- __init__.py
|   |   |-- db_retrieval_state.py
|   |   |-- memory.py
|   |   |-- parent_state.py
|   |   `-- rag_state.py
|   |-- nodes/
|   |   |-- DBRetrieval/
|   |   |   |-- KGdb/
|   |   |   |   |-- hardcoded-graphs/
|   |   |   |   |   |-- BimDB.cypher
|   |   |   |   |   |-- insertions.cypher
|   |   |   |   |   |-- sample_queries.cypher
|   |   |   |   |   `-- schema.md
|   |   |   |   |-- __init__.py
|   |   |   |   |-- kuzu_client.py
|   |   |   |   |-- project_metadata.py
|   |   |   |   |-- retrievers.py
|   |   |   |   `-- supabase_client.py
|   |   |   |-- SQLdb/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- answer.py
|   |   |   |   |-- correct.py
|   |   |   |   |-- grade.py
|   |   |   |   |-- image_nodes.py
|   |   |   |   |-- rag_plan.py
|   |   |   |   |-- rag_router.py
|   |   |   |   |-- retrieve.py
|   |   |   |   `-- verify.py
|   |   |   |-- __init__.py
|   |   |   `-- answer.py
|   |   |-- DesktopAgent/
|   |   |   |-- __init__.py
|   |   |   `-- desktop_router.py
|   |   |-- WebCalcs/
|   |   |   |-- __init__.py
|   |   |   `-- web_router.py
|   |   |-- __init__.py
|   |   |-- desktop_router.py
|   |   |-- plan.py
|   |   |-- router_dispatcher.py
|   |   `-- web_router.py
|   |-- prompts/
|   |   |-- __init__.py
|   |   |-- desktop_router_prompts.py
|   |   |-- grading_prompts.py
|   |   |-- planner_prompts.py
|   |   |-- rag_planner_prompts.py
|   |   |-- router_prompts.py
|   |   |-- router_selection_prompts.py
|   |   |-- synthesis_prompts.py
|   |   |-- verify_prompts.py
|   |   `-- web_router_prompts.py
|   |-- references/
|   |   |-- .gitkeep
|   |   |-- planner_playbook.md
|   |   `-- project_categories.md
|   |-- renderer-update/
|   |   |-- index.html
|   |   |-- renderer.js
|   |   |-- style.css
|   |   `-- version.json
|   |-- sid_text2sql/
|   |   |-- api.py
|   |   |-- ARCHITECTURE.md
|   |   |-- assistant.py
|   |   |-- example_usage.py
|   |   |-- frontend.py
|   |   |-- prompts.py
|   |   |-- QUICKSTART.md
|   |   |-- README.md
|   |   |-- requirements.txt
|   |   |-- schema.sql
|   |   |-- test_interactive.py
|   |   `-- tools.py
|   |-- synthesis/
|   |   |-- __init__.py
|   |   `-- synthesizer.py
|   |-- thinking/
|   |   |-- execution_state.py
|   |   |-- intelligent_log_generator.py
|   |   |-- llm_thinking_generator.py
|   |   `-- rag_wrapper.py
|   |-- utils/
|   |   |-- __init__.py
|   |   |-- filters.py
|   |   |-- mmr.py
|   |   |-- plan_executor.py
|   |   |-- project_utils.py
|   |   `-- role_utils.py
|   |-- api_server.py
|   |-- CHECKPOINTER_SETUP.md
|   |-- KuzuReadme.md
|   |-- main.py
|   |-- mcp-config.json
|   |-- MEMORY_FLOW_EXPLANATION.md
|   |-- setup_references.py
|   |-- SUBGRAPH_RECOMMENDATIONS.md
|   |-- test_gemini_connection.py
|   |-- test_imports.py
|   |-- test_setup.py
|   `-- TESTING_GUIDE.md
|-- Docs/
|   `-- Miscellaneous/
|       `-- James/
|           |-- ARCHITECTURE.md
|           |-- Archprelim.md
|           |-- CORS_EXPLANATION.md
|           |-- DECISION_PIPELINE.md
|           |-- explanation.txt
|           `-- interupt_flow.md
|-- Frontend/
|   |-- agents/
|   |   |-- agents/
|   |   |   |-- __init__.py
|   |   |   |-- base_agent.py
|   |   |   |-- design_orchestrator.py
|   |   |   |-- draft_orchestrator.py
|   |   |   |-- search_orchestrator.py
|   |   |   |-- search_orchestratorr1.py
|   |   |   `-- team_orchestrator.py
|   |   |-- cognition/
|   |   |   |-- __init__.py
|   |   |   `-- planner.py
|   |   |-- core/
|   |   |   |-- execution_graphs/
|   |   |   |   |-- retrieve_db_info.graph.md
|   |   |   |   `-- written_work_analysis.graph.md
|   |   |   |-- planner/
|   |   |   |   |-- intent_catalog.md
|   |   |   |   `-- scenario_router.md
|   |   |   |-- plans/
|   |   |   |   |-- retrieve_db_info.plan.md
|   |   |   |   `-- written_work_improvement.plan.md
|   |   |   |-- runtime/
|   |   |   |   |-- ai_executor.py
|   |   |   |   |-- dry_run.py
|   |   |   |   |-- load_specs.py
|   |   |   |   `-- route_query.py
|   |   |   |-- scenarios/
|   |   |   |   |-- find_past_project.md
|   |   |   |   `-- rfp_response.md
|   |   |   `-- capability_registry.py
|   |   |-- execution/
|   |   |   |-- __init__.py
|   |   |   `-- trace.py
|   |   |-- tools/
|   |   |   |-- __init__.py
|   |   |   |-- calculation_tools.py
|   |   |   `-- search_tools.py
|   |   |-- ARCHITECTURE_MULTI_AGENT.md
|   |   |-- demo_cache.json
|   |   |-- demo_cache.py
|   |   |-- explain.txt
|   |   `-- run_multi_agent.py
|   |-- backend/
|   |   |-- main.py
|   |   |-- README.md
|   |   |-- requirements.txt
|   |   |-- run.bat
|   |   |-- run.sh
|   |   `-- SETUP_COMPLETE.md
|   |-- Frontend/
|   |   |-- assets/
|   |   |   `-- css/
|   |   |       `-- main.css
|   |   |-- components/
|   |   |   |-- icons/
|   |   |   |   |-- BrainIcon.vue
|   |   |   |   |-- ChatIcon.vue
|   |   |   |   |-- ClipboardIcon.vue
|   |   |   |   |-- ClockIcon.vue
|   |   |   |   |-- FolderIcon.vue
|   |   |   |   |-- GearIcon.vue
|   |   |   |   `-- HouseIcon.vue
|   |   |   |-- tabs/
|   |   |   |   |-- BimViewerTab.vue
|   |   |   |   |-- DocumentIntelligenceTab.vue
|   |   |   |   |-- EmployeeTrackingTab.vue
|   |   |   |   `-- OverviewTab.vue
|   |   |   |-- views/
|   |   |   |   |-- DiscussionView.vue
|   |   |   |   |-- SettingsView.vue
|   |   |   |   |-- TimesheetView.vue
|   |   |   |   |-- TodoListView.vue
|   |   |   |   `-- WorkView.vue
|   |   |   |-- AgentLogsPanel.vue
|   |   |   |-- ChatInterface.vue
|   |   |   |-- DocumentChatInterface.vue
|   |   |   |-- DocumentListPanel.vue
|   |   |   |-- DraftEditor.vue
|   |   |   |-- EmployeeCard.vue
|   |   |   |-- PDFViewer.vue
|   |   |   |-- SmartChatPanel.vue
|   |   |   |-- SpeckleViewer.vue
|   |   |   |-- TimeScaleToggle.vue
|   |   |   `-- WelcomeScreen.vue
|   |   |-- composables/
|   |   |   |-- useAuth.ts
|   |   |   |-- useChat.ts
|   |   |   |-- useIFCUpload.ts
|   |   |   |-- useMessageFormatter.ts
|   |   |   |-- useModelDesignWorkflow.ts
|   |   |   |-- useProjectMapping.ts
|   |   |   |-- useResizable.ts
|   |   |   |-- useRFPProposalWorkflow.ts
|   |   |   |-- useRFPWorkflow.ts
|   |   |   |-- useSmartChat.ts
|   |   |   |-- useSpeckle.ts
|   |   |   |-- useViewer.ts
|   |   |   `-- useWorkspace.ts
|   |   |-- data/
|   |   |   |-- employees.ts
|   |   |   |-- projectInsights.ts
|   |   |   `-- timeTracking.ts
|   |   |-- lib/
|   |   |   `-- viewer/
|   |   |       `-- helpers.ts
|   |   |-- middleware/
|   |   |   `-- root-redirect.global.ts
|   |   |-- pages/
|   |   |   |-- app.vue
|   |   |   |-- index.vue
|   |   |   |-- loading.vue
|   |   |   |-- login.vue
|   |   |   `-- workspace.vue
|   |   |-- public/
|   |   |   |-- writing/
|   |   |   |   |-- finalword.txt
|   |   |   |   |-- keypoint.txt
|   |   |   |   |-- Multi-level parking Garage.docx
|   |   |   |   |-- Multi-level parking Garage.pdf
|   |   |   |   |-- RESPONSE TO RFP (1) (1).docx
|   |   |   |   |-- RESPONSE TO RFP (1) (1).pdf
|   |   |   |   |-- sampleprojects.txt
|   |   |   |   |-- Structural Engineer RFP 63023.pdf
|   |   |   |   |-- Template Proposal.docx
|   |   |   |   `-- Template Proposal.pdf
|   |   |   `-- favicon.svg
|   |   |-- .gitignore
|   |   |-- app.vue
|   |   |-- DEMO_SCRIPT.md
|   |   |-- eslint.config.mjs
|   |   |-- nuxt.config.ts
|   |   |-- package.json
|   |   |-- postcss.config.js
|   |   |-- QUICK_START.md
|   |   |-- README.md
|   |   |-- SETUP.md
|   |   |-- tailwind.config.js
|   |   `-- tsconfig.json
|   |-- .gitignore
|   `-- BACKEND_SETUP.md
|-- Local Agent/
|   |-- Connector/
|   |   |-- .circleci/
|   |   |   |-- scripts/
|   |   |   |   |-- common-jobs.yml
|   |   |   |   |-- config-generator.py
|   |   |   |   |-- config-template.yml
|   |   |   |   |-- connector-jobs.yml
|   |   |   |   `-- parameters.json
|   |   |   `-- config.yml
|   |   |-- .config/
|   |   |   `-- dotnet-tools.json
|   |   |-- .github/
|   |   |   |-- ISSUE_TEMPLATE/
|   |   |   |   |-- bug_report.md
|   |   |   |   |-- feature_request.md
|   |   |   |   `-- papercut.md
|   |   |   |-- CODE_OF_CONDUCT.md
|   |   |   |-- CODEOWNERS
|   |   |   |-- CONTRIBUTING.md
|   |   |   `-- pull_request_template.md
|   |   |-- .husky/
|   |   |   |-- pre-commit
|   |   |   `-- task-runner.json
|   |   |-- Automate/
|   |   |   |-- Speckle.Automate.Sdk/
|   |   |   |   |-- DataAnnotations/
|   |   |   |   |   `-- SecretAttribute.cs
|   |   |   |   |-- Schema/
|   |   |   |   |   |-- Triggers/
|   |   |   |   |   |   |-- AutomationRunTriggerBase.cs
|   |   |   |   |   |   `-- VersionCreationTrigger.cs
|   |   |   |   |   |-- AutomationResult.cs
|   |   |   |   |   |-- AutomationRunData.cs
|   |   |   |   |   |-- AutomationStatus.cs
|   |   |   |   |   |-- AutomationStatusMapping.cs
|   |   |   |   |   |-- BlobUploadResponse.cs
|   |   |   |   |   |-- FunctionRunData.cs
|   |   |   |   |   |-- FunctionRunDataParser.cs
|   |   |   |   |   |-- ObjectResultLevel.cs
|   |   |   |   |   |-- ObjectResultLevelMapping.cs
|   |   |   |   |   |-- ObjectResults.cs
|   |   |   |   |   |-- ObjectResultValues.cs
|   |   |   |   |   |-- ResultCase.cs
|   |   |   |   |   `-- UploadResult.cs
|   |   |   |   |-- Test/
|   |   |   |   |   |-- TestAutomateEnvironment.cs
|   |   |   |   |   `-- TestAutomateUtils.cs
|   |   |   |   |-- AutomationContext.cs
|   |   |   |   |-- Runner.cs
|   |   |   |   `-- Speckle.Automate.Sdk.csproj
|   |   |   `-- Tests/
|   |   |       `-- Speckle.Automate.Sdk.Tests.Integration/
|   |   |           |-- GetAutomationStatus.cs
|   |   |           |-- GlobalUsings.cs
|   |   |           |-- README.md
|   |   |           |-- Speckle.Automate.Sdk.Tests.Integration.csproj
|   |   |           |-- SpeckleAutomate.cs
|   |   |           |-- TestAutomateFunction.cs
|   |   |           `-- TestAutomateUtils.cs
|   |   |-- ConnectorArchicad/
|   |   |   |-- AddOn/
|   |   |   |   |-- Sources/
|   |   |   |   |   |-- AddOn/
|   |   |   |   |   |   |-- Commands/
|   |   |   |   |   |   |   |-- BaseCommand.cpp
|   |   |   |   |   |   |   |-- BaseCommand.hpp
|   |   |   |   |   |   |   |-- CommandHelpers.hpp
|   |   |   |   |   |   |   |-- CreateBeam.cpp
|   |   |   |   |   |   |   |-- CreateBeam.hpp
|   |   |   |   |   |   |   |-- CreateColumn.cpp
|   |   |   |   |   |   |   |-- CreateColumn.hpp
|   |   |   |   |   |   |   |-- CreateCommand.cpp
|   |   |   |   |   |   |   |-- CreateCommand.hpp
|   |   |   |   |   |   |   |-- CreateDirectShape.cpp
|   |   |   |   |   |   |   |-- CreateDirectShape.hpp
|   |   |   |   |   |   |   |-- CreateDoor.cpp
|   |   |   |   |   |   |   |-- CreateDoor.hpp
|   |   |   |   |   |   |   |-- CreateGridElement.cpp
|   |   |   |   |   |   |   |-- CreateGridElement.hpp
|   |   |   |   |   |   |   |-- CreateObject.cpp
|   |   |   |   |   |   |   |-- CreateObject.hpp
|   |   |   |   |   |   |   |-- CreateOpening.cpp
|   |   |   |   |   |   |   |-- CreateOpening.hpp
|   |   |   |   |   |   |   |-- CreateOpeningBase.cpp
|   |   |   |   |   |   |   |-- CreateOpeningBase.hpp
|   |   |   |   |   |   |   |-- CreateRoof.cpp
|   |   |   |   |   |   |   |-- CreateRoof.hpp
|   |   |   |   |   |   |   |-- CreateShell.cpp
|   |   |   |   |   |   |   |-- CreateShell.hpp
|   |   |   |   |   |   |   |-- CreateSkylight.cpp
|   |   |   |   |   |   |   |-- CreateSkylight.hpp
|   |   |   |   |   |   |   |-- CreateSlab.cpp
|   |   |   |   |   |   |   |-- CreateSlab.hpp
|   |   |   |   |   |   |   |-- CreateWall.cpp
|   |   |   |   |   |   |   |-- CreateWall.hpp
|   |   |   |   |   |   |   |-- CreateWindow.cpp
|   |   |   |   |   |   |   |-- CreateWindow.hpp
|   |   |   |   |   |   |   |-- CreateZone.cpp
|   |   |   |   |   |   |   |-- CreateZone.hpp
|   |   |   |   |   |   |   |-- FinishReceiveTransaction.cpp
|   |   |   |   |   |   |   |-- FinishReceiveTransaction.hpp
|   |   |   |   |   |   |   |-- GetBeamData.cpp
|   |   |   |   |   |   |   |-- GetBeamData.hpp
|   |   |   |   |   |   |   |-- GetColumnData.cpp
|   |   |   |   |   |   |   |-- GetColumnData.hpp
|   |   |   |   |   |   |   |-- GetDataCommand.cpp
|   |   |   |   |   |   |   |-- GetDataCommand.hpp
|   |   |   |   |   |   |   |-- GetDoorData.cpp
|   |   |   |   |   |   |   |-- GetDoorData.hpp
|   |   |   |   |   |   |   |-- GetElementBaseData.cpp
|   |   |   |   |   |   |   |-- GetElementBaseData.hpp
|   |   |   |   |   |   |   |-- GetElementIds.cpp
|   |   |   |   |   |   |   |-- GetElementIds.hpp
|   |   |   |   |   |   |   |-- GetElementTypes.cpp
|   |   |   |   |   |   |   |-- GetElementTypes.hpp
|   |   |   |   |   |   |   |-- GetGridElementData.cpp
|   |   |   |   |   |   |   |-- GetGridElementData.hpp
|   |   |   |   |   |   |   |-- GetModelForElements.cpp
|   |   |   |   |   |   |   |-- GetModelForElements.hpp
|   |   |   |   |   |   |   |-- GetObjectData.cpp
|   |   |   |   |   |   |   |-- GetObjectData.hpp
|   |   |   |   |   |   |   |-- GetOpeningBaseData.hpp
|   |   |   |   |   |   |   |-- GetOpeningData.cpp
|   |   |   |   |   |   |   |-- GetOpeningData.hpp
|   |   |   |   |   |   |   |-- GetProjectInfo.cpp
|   |   |   |   |   |   |   |-- GetProjectInfo.hpp
|   |   |   |   |   |   |   |-- GetRoofData.cpp
|   |   |   |   |   |   |   |-- GetRoofData.hpp
|   |   |   |   |   |   |   |-- GetShellData.cpp
|   |   |   |   |   |   |   |-- GetShellData.hpp
|   |   |   |   |   |   |   |-- GetSkylightData.cpp
|   |   |   |   |   |   |   |-- GetSkylightData.hpp
|   |   |   |   |   |   |   |-- GetSlabData.cpp
|   |   |   |   |   |   |   |-- GetSlabData.hpp
|   |   |   |   |   |   |   |-- GetWallData.cpp
|   |   |   |   |   |   |   |-- GetWallData.hpp
|   |   |   |   |   |   |   |-- GetWindowData.cpp
|   |   |   |   |   |   |   |-- GetWindowData.hpp
|   |   |   |   |   |   |   |-- GetZoneData.cpp
|   |   |   |   |   |   |   |-- GetZoneData.hpp
|   |   |   |   |   |   |   |-- SelectElements.cpp
|   |   |   |   |   |   |   `-- SelectElements.hpp
|   |   |   |   |   |   |-- Objects/
|   |   |   |   |   |   |   |-- Level.cpp
|   |   |   |   |   |   |   |-- Level.hpp
|   |   |   |   |   |   |   |-- ModelInfo.cpp
|   |   |   |   |   |   |   |-- ModelInfo.hpp
|   |   |   |   |   |   |   |-- Point.cpp
|   |   |   |   |   |   |   |-- Point.hpp
|   |   |   |   |   |   |   |-- Polyline.cpp
|   |   |   |   |   |   |   |-- Polyline.hpp
|   |   |   |   |   |   |   |-- Vector.cpp
|   |   |   |   |   |   |   `-- Vector.hpp
|   |   |   |   |   |   |-- AddOnMain.cpp
|   |   |   |   |   |   |-- APIEnvir.h
|   |   |   |   |   |   |-- APIMigrationHelper.hpp
|   |   |   |   |   |   |-- AttributeManager.cpp
|   |   |   |   |   |   |-- AttributeManager.hpp
|   |   |   |   |   |   |-- ClassificationImportManager.cpp
|   |   |   |   |   |   |-- ClassificationImportManager.hpp
|   |   |   |   |   |   |-- Database.cpp
|   |   |   |   |   |   |-- Database.hpp
|   |   |   |   |   |   |-- ExchangeManager.cpp
|   |   |   |   |   |   |-- ExchangeManager.hpp
|   |   |   |   |   |   |-- FieldNames.hpp
|   |   |   |   |   |   |-- LibpartImportManager.cpp
|   |   |   |   |   |   |-- LibpartImportManager.hpp
|   |   |   |   |   |   |-- PropertyExportManager.cpp
|   |   |   |   |   |   |-- PropertyExportManager.hpp
|   |   |   |   |   |   |-- ResourceIds.hpp
|   |   |   |   |   |   |-- ResourceStrings.cpp
|   |   |   |   |   |   |-- ResourceStrings.hpp
|   |   |   |   |   |   |-- TypeNameTables.cpp
|   |   |   |   |   |   |-- TypeNameTables.hpp
|   |   |   |   |   |   |-- Utility.cpp
|   |   |   |   |   |   `-- Utility.hpp
|   |   |   |   |   |-- AddOnResources/
|   |   |   |   |   |   |-- RFIX/
|   |   |   |   |   |   |   |-- Images/
|   |   |   |   |   |   |   |   |-- AddOnIconMac_18x18.svg
|   |   |   |   |   |   |   |   `-- AddOnIconWin_18x18.svg
|   |   |   |   |   |   |   `-- AddOnFix.grc
|   |   |   |   |   |   |-- RFIX.mac/
|   |   |   |   |   |   |   `-- Info.plist
|   |   |   |   |   |   |-- RFIX.win/
|   |   |   |   |   |   |   `-- AddOnMain.rc2
|   |   |   |   |   |   |-- RINT/
|   |   |   |   |   |   |   `-- AddOn.grc
|   |   |   |   |   |   |-- Tools/
|   |   |   |   |   |   |   `-- CompileResources.py
|   |   |   |   |   |   `-- ResourceMDIDIds.hpp.in
|   |   |   |   |   `-- .editorconfig
|   |   |   |   |-- CMakeLists.txt
|   |   |   |   `-- README.md
|   |   |   |-- ConnectorArchicad/
|   |   |   |   |-- Assets/
|   |   |   |   |   |-- icon-mac.icns
|   |   |   |   |   `-- icon.ico
|   |   |   |   |-- Communication/
|   |   |   |   |   |-- Commands/
|   |   |   |   |   |   |-- Command_CreateBeam.cs
|   |   |   |   |   |   |-- Command_CreateColumn.cs
|   |   |   |   |   |   |-- Command_CreateDirectShape.cs
|   |   |   |   |   |   |-- Command_CreateDoor.cs
|   |   |   |   |   |   |-- Command_CreateFloor.cs
|   |   |   |   |   |   |-- Command_CreateGridElement.cs
|   |   |   |   |   |   |-- Command_CreateObject.cs
|   |   |   |   |   |   |-- Command_CreateOpening.cs
|   |   |   |   |   |   |-- Command_CreateRoof.cs
|   |   |   |   |   |   |-- Command_CreateRoom.cs
|   |   |   |   |   |   |-- Command_CreateShell.cs
|   |   |   |   |   |   |-- Command_CreateSkylight.cs
|   |   |   |   |   |   |-- Command_CreateWall.cs
|   |   |   |   |   |   |-- Command_CreateWindow.cs
|   |   |   |   |   |   |-- Command_FinishReceiveTransaction.cs
|   |   |   |   |   |   |-- Command_GetBeamData.cs
|   |   |   |   |   |   |-- Command_GetColumnData.cs
|   |   |   |   |   |   |-- Command_GetDataBase.cs
|   |   |   |   |   |   |-- Command_GetDoorData.cs
|   |   |   |   |   |   |-- Command_GetElementBaseData.cs
|   |   |   |   |   |   |-- Command_GetElementIds.cs
|   |   |   |   |   |   |-- Command_GetElementType.cs
|   |   |   |   |   |   |-- Command_GetFloorData.cs
|   |   |   |   |   |   |-- Command_GetGridElementData.cs
|   |   |   |   |   |   |-- Command_GetModelOfElements.cs
|   |   |   |   |   |   |-- Command_GetObjectData.cs
|   |   |   |   |   |   |-- Command_GetOpening.cs
|   |   |   |   |   |   |-- Command_GetProjectInfo.cs
|   |   |   |   |   |   |-- Command_GetRoofData.cs
|   |   |   |   |   |   |-- Command_GetRoomData.cs
|   |   |   |   |   |   |-- Command_GetShellData.cs
|   |   |   |   |   |   |-- Command_GetSkylightData.cs
|   |   |   |   |   |   |-- Command_GetWallData.cs
|   |   |   |   |   |   |-- Command_GetWindowData.cs
|   |   |   |   |   |   |-- Command_SelectElements.cs
|   |   |   |   |   |   `-- ICommand.cs
|   |   |   |   |   |-- AsyncCommandProcessor.cs
|   |   |   |   |   |-- CommandRequest.cs
|   |   |   |   |   |-- CommandResponse.cs
|   |   |   |   |   |-- ConnectionManager.cs
|   |   |   |   |   `-- HttpCommandExecutor.cs
|   |   |   |   |-- Converters/
|   |   |   |   |   |-- Converters/
|   |   |   |   |   |   |-- BeamConverter.cs
|   |   |   |   |   |   |-- ColumnConverter.cs
|   |   |   |   |   |   |-- DirectShapeConverter.cs
|   |   |   |   |   |   |-- DoorConverter.cs
|   |   |   |   |   |   |-- FloorConverter.cs
|   |   |   |   |   |   |-- GridLineConverter.cs
|   |   |   |   |   |   |-- IElementConverter.cs
|   |   |   |   |   |   |-- ObjectConverter.cs
|   |   |   |   |   |   |-- OpeningConverter.cs
|   |   |   |   |   |   |-- RoofConverter.cs
|   |   |   |   |   |   |-- RoomConverter.cs
|   |   |   |   |   |   |-- SkylightConverter.cs
|   |   |   |   |   |   |-- Utils.cs
|   |   |   |   |   |   |-- WallConverter.cs
|   |   |   |   |   |   `-- WindowConverter.cs
|   |   |   |   |   |-- ConversionOptions.cs
|   |   |   |   |   |-- ConverterArchicad.cs
|   |   |   |   |   |-- ElementConverterManager.cs
|   |   |   |   |   |-- ElementConverterManagerReceive.cs
|   |   |   |   |   |-- ElementTypeProvider.cs
|   |   |   |   |   `-- ModelConverter.cs
|   |   |   |   |-- Elements/
|   |   |   |   |   |-- GridElement.cs
|   |   |   |   |   |-- Object.cs
|   |   |   |   |   `-- Room.cs
|   |   |   |   |-- Helpers/
|   |   |   |   |   `-- Timer.cs
|   |   |   |   |-- Model/
|   |   |   |   |   |-- ElementModelData.cs
|   |   |   |   |   |-- MeshModel.cs
|   |   |   |   |   `-- ProjectInfoData.cs
|   |   |   |   |-- Properties/
|   |   |   |   |   |-- launchSettings.json
|   |   |   |   |   |-- OperationNameTemplates.Designer.cs
|   |   |   |   |   `-- OperationNameTemplates.resx
|   |   |   |   |-- UI/
|   |   |   |   |   |-- ConnectorBinding.Selection.cs
|   |   |   |   |   `-- ConnectorBinding.Settings.cs
|   |   |   |   |-- ConnectorArchicad.csproj
|   |   |   |   |-- ConnectorBinding.cs
|   |   |   |   |-- Info.plist
|   |   |   |   `-- Program.cs
|   |   |   |-- ConnectorArchicad.sln
|   |   |   |-- ConnectorArchicad.slnf
|   |   |   |-- LICENSE
|   |   |   `-- README.md
|   |   |-- ConnectorAutocadCivil/
|   |   |   |-- AdvanceSteelAddinRegistrator/
|   |   |   |   |-- AdvanceSteelAddinRegistrator.csproj
|   |   |   |   |-- App.config
|   |   |   |   |-- Program.cs
|   |   |   |   |-- Schema.cs
|   |   |   |   `-- Schema.xsd
|   |   |   |-- ConnectorAdvanceSteel2023/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   |-- ConnectorAdvanceSteel2023.csproj
|   |   |   |   `-- MyAddons.xml
|   |   |   |-- ConnectorAdvanceSteel2024/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   |-- ConnectorAdvanceSteel2024.csproj
|   |   |   |   `-- MyAddons.xml
|   |   |   |-- ConnectorAutocad2021/
|   |   |   |   `-- ConnectorAutocad2021.csproj
|   |   |   |-- ConnectorAutocad2022/
|   |   |   |   `-- ConnectorAutocad2022.csproj
|   |   |   |-- ConnectorAutocad2023/
|   |   |   |   `-- ConnectorAutocad2023.csproj
|   |   |   |-- ConnectorAutocad2024/
|   |   |   |   `-- ConnectorAutocad2024.csproj
|   |   |   |-- ConnectorAutocad2025/
|   |   |   |   `-- ConnectorAutocad2025.csproj
|   |   |   |-- ConnectorAutocadCivil/
|   |   |   |   |-- DocumentUtils/
|   |   |   |   |   `-- TransactionContext.cs
|   |   |   |   |-- Entry/
|   |   |   |   |   |-- App.cs
|   |   |   |   |   `-- SpeckleAutocadCommand.cs
|   |   |   |   |-- Storage/
|   |   |   |   |   `-- SpeckleStreamManager.cs
|   |   |   |   |-- UI/
|   |   |   |   |   |-- ConnectorBindingsAutocadCivil.cs
|   |   |   |   |   |-- ConnectorBindingsAutocadCivil.Events.cs
|   |   |   |   |   |-- ConnectorBindingsAutocadCivil.Previews.cs
|   |   |   |   |   |-- ConnectorBindingsAutocadCivil.Receive.cs
|   |   |   |   |   |-- ConnectorBindingsAutocadCivil.Selection.cs
|   |   |   |   |   `-- ConnectorBindingsAutocadCivil.Send.cs
|   |   |   |   |-- ConnectorAutocadCivilShared.projitems
|   |   |   |   |-- ConnectorAutocadCivilShared.shproj
|   |   |   |   `-- Utils.cs
|   |   |   |-- ConnectorCivil2021/
|   |   |   |   `-- ConnectorCivil2021.csproj
|   |   |   |-- ConnectorCivil2022/
|   |   |   |   `-- ConnectorCivil2022.csproj
|   |   |   |-- ConnectorCivil2023/
|   |   |   |   `-- ConnectorCivil2023.csproj
|   |   |   |-- ConnectorCivil2024/
|   |   |   |   `-- ConnectorCivil2024.csproj
|   |   |   |-- ConnectorCivil2025/
|   |   |   |   `-- ConnectorCivil2025.csproj
|   |   |   |-- ConnectorAdvanceSteel.slnf
|   |   |   |-- ConnectorAutocadCivil.sln
|   |   |   |-- ConnectorAutocadCivil.slnf
|   |   |   `-- README.md
|   |   |-- ConnectorBentley/
|   |   |   |-- ConnectorBentleyShared/
|   |   |   |   |-- Entry/
|   |   |   |   |   |-- App.cs
|   |   |   |   |   `-- SpeckleBentleyCommand.cs
|   |   |   |   |-- Resources/
|   |   |   |   |   `-- s2block.ico
|   |   |   |   |-- Storage/
|   |   |   |   |   `-- StreamStateManager.cs
|   |   |   |   |-- UI/
|   |   |   |   |   `-- Bindings.cs
|   |   |   |   |-- commands.xml
|   |   |   |   |-- ConnectorBentleyShared.projitems
|   |   |   |   |-- ConnectorBentleyShared.shproj
|   |   |   |   |-- Keyins.cs
|   |   |   |   `-- Utils.cs
|   |   |   |-- ConnectorMicroStation/
|   |   |   |   |-- app.config
|   |   |   |   |-- ConnectorMicroStation.csproj
|   |   |   |   |-- ConnectorMicroStationRibbon.xml
|   |   |   |   `-- Speckle2MicroStation.cfg
|   |   |   |-- ConnectorOpenBuildings/
|   |   |   |   |-- ConnectorOpenBuildings.csproj
|   |   |   |   |-- ConnectorOpenBuildingsRibbon.xml
|   |   |   |   `-- Speckle2OpenBuildings.cfg
|   |   |   |-- ConnectorOpenRail/
|   |   |   |   |-- ConnectorOpenRail.csproj
|   |   |   |   |-- ConnectorOpenRailRibbon.xml
|   |   |   |   `-- Speckle2OpenRail.cfg
|   |   |   |-- ConnectorOpenRoads/
|   |   |   |   |-- ConnectorOpenRoads.csproj
|   |   |   |   |-- ConnectorOpenRoadsRibbon.xml
|   |   |   |   `-- Speckle2OpenRoads.cfg
|   |   |   |-- ConnectorBentley.sln
|   |   |   |-- ConnectorBentley.slnf
|   |   |   `-- README.md
|   |   |-- ConnectorCore/
|   |   |   `-- DllConflictManagement/
|   |   |       |-- Analytics/
|   |   |       |   |-- AnalyticsWithoutDependencies.cs
|   |   |       |   `-- Events.cs
|   |   |       |-- ConflictManagementOptions/
|   |   |       |   |-- DllConflictManagmentOptions.cs
|   |   |       |   `-- DllConflictManagmentOptionsLoader.cs
|   |   |       |-- EventEmitter/
|   |   |       |   |-- ActionEventArgs.cs
|   |   |       |   |-- DllConflictEventEmitter.cs
|   |   |       |   `-- LoggingEventArgs.cs
|   |   |       |-- Serialization/
|   |   |       |   |-- ISerializer.cs
|   |   |       |   `-- SpeckleNewtonsoftSerializer.cs
|   |   |       |-- AssemblyConflictInfo.cs
|   |   |       |-- AssemblyConflictInfoDto.cs
|   |   |       |-- DllConflictManagement.csproj
|   |   |       |-- DllConflictManager.cs
|   |   |       `-- DllConflictUserNotifier.cs
|   |   |-- ConnectorCSI/
|   |   |   |-- ConnectorCSIBridge/
|   |   |   |   |-- app.config
|   |   |   |   `-- ConnectorCSIBridge.csproj
|   |   |   |-- ConnectorCSIShared/
|   |   |   |   |-- StreamStateManager/
|   |   |   |   |   `-- StreamStateManager.cs
|   |   |   |   |-- UI/
|   |   |   |   |   |-- ConnectorBindingsCSI.ClientOperations.cs
|   |   |   |   |   |-- ConnectorBindingsCSI.cs
|   |   |   |   |   |-- ConnectorBindingsCSI.Recieve.cs
|   |   |   |   |   |-- ConnectorBindingsCSI.Selection.cs
|   |   |   |   |   |-- ConnectorBindingsCSI.Send.cs
|   |   |   |   |   `-- ConnectorBindingsCSI.Settings.cs
|   |   |   |   |-- Util/
|   |   |   |   |   |-- ConnectorCSIUtils.cs
|   |   |   |   |   `-- ResultUtils.cs
|   |   |   |   |-- ConnectorCSIShared.projitems
|   |   |   |   |-- ConnectorCSIShared.shproj
|   |   |   |   |-- cPlugin.cs
|   |   |   |   `-- UnusedClass.cs
|   |   |   |-- ConnectorETABS/
|   |   |   |   `-- ConnectorETABS.csproj
|   |   |   |-- ConnectorSAFE/
|   |   |   |   `-- ConnectorSAFE.csproj
|   |   |   |-- ConnectorSAP2000/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- AssemblyInfo.cs
|   |   |   |   `-- ConnectorSAP2000.csproj
|   |   |   |-- DriverCSharp/
|   |   |   |   |-- App.config
|   |   |   |   |-- DriverCSharp.csproj
|   |   |   |   |-- PluginCallback.cs
|   |   |   |   `-- Program.cs
|   |   |   |-- DriverPluginCSharp/
|   |   |   |   |-- cPlugin.cs
|   |   |   |   `-- DriverPluginCSharp.csproj
|   |   |   |-- ConnectorCSI.sln
|   |   |   `-- ConnectorCSI.slnf
|   |   |-- ConnectorDynamo/
|   |   |   |-- ConnectorDynamo/
|   |   |   |   |-- AccountsNode/
|   |   |   |   |   |-- Accounts.cs
|   |   |   |   |   |-- AccountsUi.xaml
|   |   |   |   |   |-- AccountsUi.xaml.cs
|   |   |   |   |   `-- AccountsViewCustomization.cs
|   |   |   |   |-- CreateStreamNode/
|   |   |   |   |   |-- CreateStream.cs
|   |   |   |   |   |-- CreateStreamUi.xaml
|   |   |   |   |   |-- CreateStreamUi.xaml.cs
|   |   |   |   |   `-- CreateStreamViewCustomization.cs
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   |-- ReceiveNode/
|   |   |   |   |   |-- Receive.cs
|   |   |   |   |   |-- ReceiveUi.xaml
|   |   |   |   |   |-- ReceiveUi.xaml.cs
|   |   |   |   |   `-- ReceiveViewCustomization.cs
|   |   |   |   |-- SendNode/
|   |   |   |   |   |-- Send.cs
|   |   |   |   |   |-- SendUi.xaml
|   |   |   |   |   |-- SendUi.xaml.cs
|   |   |   |   |   `-- SendViewCustomization.cs
|   |   |   |   |-- Themes/
|   |   |   |   |   `-- Generic.xaml
|   |   |   |   |-- ValueConverters/
|   |   |   |   |   `-- BoolVisibConverter.cs
|   |   |   |   |-- ViewNode/
|   |   |   |   |   |-- View.cs
|   |   |   |   |   |-- ViewUi.xaml
|   |   |   |   |   |-- ViewUi.xaml.cs
|   |   |   |   |   `-- ViewViewCustomization.cs
|   |   |   |   |-- ConnectorDynamo.csproj
|   |   |   |   |-- DebounceTimer.cs
|   |   |   |   |-- pkg.json
|   |   |   |   |-- SpeckleConnectorDynamoImages.resources
|   |   |   |   `-- SpeckleConnectorDynamoImages.resx
|   |   |   |-- ConnectorDynamoExtension/
|   |   |   |   |-- ConnectorDynamoExtension.csproj
|   |   |   |   |-- SpeckleConnectorDynamoExtension_ViewExtensionDefinition.xml
|   |   |   |   |-- SpeckleExtension.cs
|   |   |   |   `-- SpeckleWatchHandler.cs
|   |   |   |-- ConnectorDynamoFunctions/
|   |   |   |   |-- Developer/
|   |   |   |   |   |-- Conversion.cs
|   |   |   |   |   |-- Local.cs
|   |   |   |   |   |-- Serialization.cs
|   |   |   |   |   `-- Transport.cs
|   |   |   |   |-- Account.cs
|   |   |   |   |-- AnalyticsUtils.cs
|   |   |   |   |-- Auto.cs
|   |   |   |   |-- BatchConverter.cs
|   |   |   |   |-- ConnectorDynamoFunctions.csproj
|   |   |   |   |-- Functions.cs
|   |   |   |   |-- Globals.cs
|   |   |   |   |-- Icon.cs
|   |   |   |   |-- InMemoryCache.cs
|   |   |   |   |-- OnErrorEventArgs.cs
|   |   |   |   |-- SpeckleConnectorDynamoFunctions_DynamoCustomization.xml
|   |   |   |   |-- SpeckleConnectorDynamoFunctionsImages.resources
|   |   |   |   |-- SpeckleConnectorDynamoFunctionsImages.resx
|   |   |   |   |-- SpeckleConnectorDynamoImagesFunctions.resources
|   |   |   |   |-- Stream.cs
|   |   |   |   `-- Utils.cs
|   |   |   |-- ConnectorDynamo.sln
|   |   |   |-- ConnectorDynamo.slnf
|   |   |   `-- README.md
|   |   |-- ConnectorGrasshopper/
|   |   |   |-- ConnectorGrasshopper6/
|   |   |   |   `-- ConnectorGrasshopper6.csproj
|   |   |   |-- ConnectorGrasshopper7/
|   |   |   |   `-- ConnectorGrasshopper7.csproj
|   |   |   |-- ConnectorGrasshopper8/
|   |   |   |   `-- ConnectorGrasshopper8.csproj
|   |   |   |-- ConnectorGrasshopperShared/
|   |   |   |   |-- Accounts/
|   |   |   |   |   |-- Obsolete/
|   |   |   |   |   |   |-- Accounts.AccountDetails.cs
|   |   |   |   |   |   `-- AccountsV2Upgrader.cs
|   |   |   |   |   |-- Accounts.AccountDetailsV2.cs
|   |   |   |   |   |-- Accounts.GetAccountToken.cs
|   |   |   |   |   |-- Accounts.ListAccounts.cs
|   |   |   |   |   `-- Accounts.ServerAccount.cs
|   |   |   |   |-- BaseComponents/
|   |   |   |   |   |-- ComponentTracker.cs
|   |   |   |   |   |-- GH_SpeckleAsyncComponent.cs
|   |   |   |   |   |-- GH_SpeckleComponent.cs
|   |   |   |   |   |-- GH_SpeckleTaskCapableComponent.cs
|   |   |   |   |   |-- ISpeckleTrackingComponent.cs
|   |   |   |   |   |-- SelectKitAsyncComponentBase.cs
|   |   |   |   |   |-- SelectKitComponentBase.cs
|   |   |   |   |   `-- SelectKitTaskCapableComponentBase.cs
|   |   |   |   |-- Collections/
|   |   |   |   |   |-- FlattenCollectionComponent.cs
|   |   |   |   |   |-- GH_SpeckleCollection.cs
|   |   |   |   |   `-- SpeckleCollectionParam.cs
|   |   |   |   |-- Conversion/
|   |   |   |   |   |-- DeserialiseTaskCapableComponent.cs
|   |   |   |   |   |-- SerialiseTaskCapableComponent.cs
|   |   |   |   |   |-- ToNativeTaskCapableComponent.cs
|   |   |   |   |   `-- ToSpeckleTaskCapableComponent.cs
|   |   |   |   |-- Extras/
|   |   |   |   |   |-- DebounceDispatcher.cs
|   |   |   |   |   |-- GenericAccessParam.cs
|   |   |   |   |   |-- GH_SpeckleAccount.cs
|   |   |   |   |   |-- GH_SpeckleBase.cs
|   |   |   |   |   |-- GH_SpeckleGoo.cs
|   |   |   |   |   |-- SendReceiveDataParam.cs
|   |   |   |   |   |-- SpeckleBaseParam.cs
|   |   |   |   |   |-- SpeckleStatefulParam.cs
|   |   |   |   |   |-- SpeckleStateTag.cs
|   |   |   |   |   |-- SpeckleStreamParam.cs
|   |   |   |   |   |-- SpeckleUpgradeObject.cs
|   |   |   |   |   |-- TreeBuilder.cs
|   |   |   |   |   `-- Utilities.cs
|   |   |   |   |-- Objects/
|   |   |   |   |   |-- Deprecated/
|   |   |   |   |   |   |-- CreateSpeckleObjectByKeyValueTaskComponent.cs
|   |   |   |   |   |   |-- ExpandSpeckleObjectTaskComponent.cs
|   |   |   |   |   |   |-- ExtendSpeckleObjectByKeyValueTaskComponent.cs
|   |   |   |   |   |   `-- ObjectsV2Upgrader.cs
|   |   |   |   |   |-- CreateSpeckleObjectByKeyValueV2TaskComponent.cs
|   |   |   |   |   |-- CreateSpeckleObjectTaskComponent.cs
|   |   |   |   |   |-- DeconstructSpeckleObjectTaskComponent.cs
|   |   |   |   |   |-- ExtendSpeckleObjectByKeyValueV2TaskComponent.cs
|   |   |   |   |   |-- ExtendSpeckleObjectTaskComponent.cs
|   |   |   |   |   |-- GetObjectKeysComponent.cs
|   |   |   |   |   |-- GetObjectValueByKeyTaskComponent.cs
|   |   |   |   |   `-- SpeckleObjectGroup.cs
|   |   |   |   |-- Ops/
|   |   |   |   |   |-- Deprecated/
|   |   |   |   |   |   |-- Operations.ReceiveComponent.cs
|   |   |   |   |   |   |-- Operations.ReceiveComponentSync.cs
|   |   |   |   |   |   |-- Operations.SendComponent.cs
|   |   |   |   |   |   |-- Operations.SendComponentSync.cs
|   |   |   |   |   |   |-- Operations.UpgradeUtils.cs
|   |   |   |   |   |   `-- Operations.VariableInputSendComponent.cs
|   |   |   |   |   |-- Operations.ReceiveLocalComponent.cs
|   |   |   |   |   |-- Operations.SendLocalComponent.cs
|   |   |   |   |   |-- Operations.SyncReceiveComponent.cs
|   |   |   |   |   |-- Operations.SyncSendComponent.cs
|   |   |   |   |   |-- Operations.VariableInputReceiveComponent.cs
|   |   |   |   |   `-- Operations.VariableInputSendComponent.cs
|   |   |   |   |-- Properties/
|   |   |   |   |   |-- Resources.Designer.cs
|   |   |   |   |   `-- Resources.resx
|   |   |   |   |-- SchemaBuilder/
|   |   |   |   |   |-- CreateSchemaObject.cs
|   |   |   |   |   |-- CreateSchemaObjectBase.cs
|   |   |   |   |   |-- CreateSchemaObjectDialog.cs
|   |   |   |   |   |-- CSOViewModel.cs
|   |   |   |   |   |-- SchemaBuilderGen.cs
|   |   |   |   |   `-- SchemaBuilderGen.tt
|   |   |   |   |-- Streams/
|   |   |   |   |   |-- Deprecated/
|   |   |   |   |   |   |-- StreamCreateComponent.cs
|   |   |   |   |   |   |-- StreamDetailsComponent.cs
|   |   |   |   |   |   |-- StreamGetComponent.cs
|   |   |   |   |   |   |-- StreamListComponent.cs
|   |   |   |   |   |   `-- StreamUpdateComponent.cs
|   |   |   |   |   |-- Upgraders/
|   |   |   |   |   |   `-- V2Upgraders.cs
|   |   |   |   |   |-- StreamCreateComponentV2.cs
|   |   |   |   |   |-- StreamDetailsComponentV2.cs
|   |   |   |   |   |-- StreamGetComponentV2.cs
|   |   |   |   |   |-- StreamGetWithTokenComponent.cs
|   |   |   |   |   |-- StreamListComponentV2.cs
|   |   |   |   |   `-- StreamUpdateComponentV2.cs
|   |   |   |   |-- Transports/
|   |   |   |   |   |-- SendReceiveTransport.cs
|   |   |   |   |   |-- Transports.Disk.cs
|   |   |   |   |   |-- Transports.Memory.cs
|   |   |   |   |   `-- Transports.Sqlite.cs
|   |   |   |   |-- ComponentCategories.cs
|   |   |   |   |-- ConnectorGrasshopperInfo.cs
|   |   |   |   |-- ConnectorGrasshopperShared.projitems
|   |   |   |   |-- ConnectorGrasshopperShared.shproj
|   |   |   |   |-- Loader.cs
|   |   |   |   |-- SpeckleGHSettings.cs
|   |   |   |   `-- UpgradeUtilities.cs
|   |   |   |-- ConnectorGrasshopperUtils/
|   |   |   |   |-- ConnectorGrasshopperUtils.csproj
|   |   |   |   |-- CSOUtils.cs
|   |   |   |   `-- UserInterfaceUtils.cs
|   |   |   |-- ExampleFiles/
|   |   |   |   |-- ObjectManagementNodes.ghx
|   |   |   |   |-- SendReceive.ghx
|   |   |   |   `-- StreamManagement.ghx
|   |   |   |-- ConnectorGrasshopper.sln
|   |   |   `-- README.md
|   |   |-- ConnectorNavisworks/
|   |   |   |-- ConnectorNavisworks/
|   |   |   |   |-- Bindings/
|   |   |   |   |   |-- ConnectorNavisworksBindings.Conversion.cs
|   |   |   |   |   |-- ConnectorNavisworksBindings.cs
|   |   |   |   |   |-- ConnectorNavisworksBindings.Events.cs
|   |   |   |   |   |-- ConnectorNavisworksBindings.File.cs
|   |   |   |   |   |-- ConnectorNavisworksBindings.Filters.cs
|   |   |   |   |   |-- ConnectorNavisworksBindings.Receive.cs
|   |   |   |   |   |-- ConnectorNavisworksBindings.Selections.cs
|   |   |   |   |   |-- ConnectorNavisworksBindings.Send.cs
|   |   |   |   |   `-- ConnectorNavisworksBindings.Settings.cs
|   |   |   |   |-- Entry/
|   |   |   |   |   |-- Commands.cs
|   |   |   |   |   |-- PackageContents.xml
|   |   |   |   |   |-- Ribbon.name
|   |   |   |   |   |-- Ribbon.xaml
|   |   |   |   |   |-- Ribbon.xaml.cs
|   |   |   |   |   |-- SpeckleHostPane.xaml
|   |   |   |   |   |-- SpeckleHostPane.xaml.cs
|   |   |   |   |   `-- SpeckleNavisworksCommand.cs
|   |   |   |   |-- NavisworksOptions/
|   |   |   |   |   |-- Autosave.cs
|   |   |   |   |   |-- Manager.cs
|   |   |   |   |   `-- Properties.cs
|   |   |   |   |-- Other/
|   |   |   |   |   |-- Constants.cs
|   |   |   |   |   |-- Developer.cs
|   |   |   |   |   |-- Elements.cs
|   |   |   |   |   |-- FilterTypes.cs
|   |   |   |   |   |-- Invokers.cs
|   |   |   |   |   |-- SelectionBuilder.cs
|   |   |   |   |   `-- Utilities.cs
|   |   |   |   |-- Resources/
|   |   |   |   |   |-- empty32.ico
|   |   |   |   |   |-- logo16.ico
|   |   |   |   |   |-- logo32.ico
|   |   |   |   |   |-- retry16.ico
|   |   |   |   |   `-- retry32.ico
|   |   |   |   |-- Storage/
|   |   |   |   |   `-- SpeckleStreamManager.cs
|   |   |   |   |-- ConnectorNavisworks.Shared.projitems
|   |   |   |   `-- ConnectorNavisworks.shproj
|   |   |   |-- ConnectorNavisworks2020/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorNavisworks2020.csproj
|   |   |   |-- ConnectorNavisworks2021/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorNavisworks2021.csproj
|   |   |   |-- ConnectorNavisworks2022/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorNavisworks2022.csproj
|   |   |   |-- ConnectorNavisworks2023/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorNavisworks2023.csproj
|   |   |   |-- ConnectorNavisworks2024/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorNavisworks2024.csproj
|   |   |   |-- ConnectorNavisworks2025/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorNavisworks2025.csproj
|   |   |   |-- ConnectorNavisworks.sln
|   |   |   |-- ConnectorNavisworks.slnf
|   |   |   `-- README.md
|   |   |-- ConnectorRevit/
|   |   |   |-- AutoInstaller/
|   |   |   |   |-- Distribution/
|   |   |   |   |   |-- README.txt
|   |   |   |   |   |-- Speckle Installer.lnk
|   |   |   |   |   |-- SpeckleAutoInstaller.exe.config
|   |   |   |   |   `-- START_HERE.bat
|   |   |   |   |-- Helpers/
|   |   |   |   |   |-- LogHelper.cs
|   |   |   |   |   `-- RevitDialogHandler.cs
|   |   |   |   |-- Models/
|   |   |   |   |   |-- ScheduleConfiguration.cs
|   |   |   |   |   `-- SetupData.cs
|   |   |   |   |-- Services/
|   |   |   |   |   |-- AccountSetupService.cs
|   |   |   |   |   |-- BackgroundWatcherService.cs
|   |   |   |   |   |-- InstallerService.cs
|   |   |   |   |   |-- RevitDetectionService.cs
|   |   |   |   |   `-- ScheduledBackgroundService.cs
|   |   |   |   |-- Storage/
|   |   |   |   |   `-- AutomatedSendConfig.cs
|   |   |   |   |-- UI/
|   |   |   |   |   |-- BackgroundServiceForm.cs
|   |   |   |   |   |-- CredentialPanel.cs
|   |   |   |   |   |-- FolderSelectionPanel.cs
|   |   |   |   |   |-- RevitSelectionPanel.cs
|   |   |   |   |   |-- SchedulePanel.cs
|   |   |   |   |   `-- SetupWizard.cs
|   |   |   |   |-- AutoInstaller.csproj
|   |   |   |   |-- BUILD_AND_DISTRIBUTE.md
|   |   |   |   |-- BUILD_AND_PACKAGE.ps1
|   |   |   |   |-- CopyDLLsToResources.ps1
|   |   |   |   |-- CREATE_DISTRIBUTION_PACKAGE.ps1
|   |   |   |   |-- DISTRIBUTION_GUIDE.md
|   |   |   |   |-- DLL_SETUP_GUIDE.md
|   |   |   |   |-- IMPLEMENTATION_NOTES.md
|   |   |   |   |-- NEXT_STEPS.md
|   |   |   |   |-- Program.cs
|   |   |   |   `-- README.md
|   |   |   |-- ConnectorRevit/
|   |   |   |   |-- Entry/
|   |   |   |   |   |-- App.cs
|   |   |   |   |   |-- CmdAvailabilityViews.cs
|   |   |   |   |   |-- HeadlessSendCommand.cs
|   |   |   |   |   |-- HelpCommand.cs
|   |   |   |   |   |-- RevitDllConflictUserNotifier.cs
|   |   |   |   |   |-- SchedulerCommand.cs
|   |   |   |   |   `-- SpeckleRevitCommand.cs
|   |   |   |   |-- Revit/
|   |   |   |   |   `-- FamilyLoadOption.cs
|   |   |   |   |-- Storage/
|   |   |   |   |   |-- AutomatedSendConfig.cs
|   |   |   |   |   |-- ConvertedObjectsCache.cs
|   |   |   |   |   |-- RevitDocumentAggregateCache.cs
|   |   |   |   |   |-- RevitObjectCache.cs
|   |   |   |   |   |-- StreamStateCache.cs
|   |   |   |   |   |-- StreamStateManager.cs
|   |   |   |   |   `-- UIDocumentProvider.cs
|   |   |   |   |-- TypeMapping/
|   |   |   |   |   |-- ElementTypeMapper.cs
|   |   |   |   |   |-- FamilyImporter.cs
|   |   |   |   |   |-- HostTypeContainer.cs
|   |   |   |   |   |-- RevitHostType.cs
|   |   |   |   |   |-- RevitMappingValue.cs
|   |   |   |   |   |-- SingleCategoryMap.cs
|   |   |   |   |   `-- TypeMap.cs
|   |   |   |   |-- UI/
|   |   |   |   |   |-- ConnectorBindingsRevit.cs
|   |   |   |   |   |-- ConnectorBindingsRevit.Events.cs
|   |   |   |   |   |-- ConnectorBindingsRevit.Previews.cs
|   |   |   |   |   |-- ConnectorBindingsRevit.Receive.cs
|   |   |   |   |   |-- ConnectorBindingsRevit.Selection.cs
|   |   |   |   |   |-- ConnectorBindingsRevit.Send.cs
|   |   |   |   |   |-- ConnectorBindingsRevit.Settings.cs
|   |   |   |   |   |-- HeadlessSendService.cs
|   |   |   |   |   |-- Panel.xaml
|   |   |   |   |   `-- Panel.xaml.cs
|   |   |   |   |-- ConnectorRevit.projitems
|   |   |   |   |-- ConnectorRevitShared.shproj
|   |   |   |   |-- ConnectorRevitUtils.cs
|   |   |   |   |-- RevitVersionHelper.cs
|   |   |   |   `-- SpeckleRevit2.addin
|   |   |   |-- ConnectorRevit2020/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorRevit2020.csproj
|   |   |   |-- ConnectorRevit2021/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorRevit2021.csproj
|   |   |   |-- ConnectorRevit2022/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorRevit2022.csproj
|   |   |   |-- ConnectorRevit2023/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorRevit2023.csproj
|   |   |   |-- ConnectorRevit2024/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorRevit2024.csproj
|   |   |   |-- ConnectorRevit2025/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   |-- ConnectorRevit2025.csproj
|   |   |   |   `-- ConnectorRevit2025.sln
|   |   |   |-- ConnectorRevit2026/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorRevit2026.csproj
|   |   |   |-- RevitSharedResources/
|   |   |   |   |-- Extensions/
|   |   |   |   |   `-- SpeckleExtensions/
|   |   |   |   |       |-- ILoggerExtensions.cs
|   |   |   |   |       |-- IRevitDocumentAggregateCacheExtensions.cs
|   |   |   |   |       `-- IRevitObjectCacheExtensions.cs
|   |   |   |   |-- Helpers/
|   |   |   |   |   |-- Categories.cs
|   |   |   |   |   |-- Extensions.cs
|   |   |   |   |   `-- RevitCategoryInfo.cs
|   |   |   |   |-- Interfaces/
|   |   |   |   |   |-- IAllRevitCategories.cs
|   |   |   |   |   |-- IAllRevitCategoriesExposer.cs
|   |   |   |   |   |-- IConvertedObjectsCache.cs
|   |   |   |   |   |-- IReceivedObjectIdMap.cs
|   |   |   |   |   |-- IRevitCategoryInfo.cs
|   |   |   |   |   |-- IRevitCommitObjectBuilder.cs
|   |   |   |   |   |-- IRevitCommitObjectBuilderExposer.cs
|   |   |   |   |   |-- IRevitDocumentAggregateCache.cs
|   |   |   |   |   |-- IRevitElementTypeRetriever.cs
|   |   |   |   |   `-- IRevitObjectCache.cs
|   |   |   |   |-- Models/
|   |   |   |   |   |-- APIContext.cs
|   |   |   |   |   |-- ConversionNotReadyCacheData.cs
|   |   |   |   |   |-- ErrorEater.cs
|   |   |   |   |   |-- RevitConverterState.cs
|   |   |   |   |   `-- TransactionManager.cs
|   |   |   |   |-- RevitSharedResources.projitems
|   |   |   |   `-- RevitSharedResources.shproj
|   |   |   |-- RevitSharedResources2020/
|   |   |   |   `-- RevitSharedResources2020.csproj
|   |   |   |-- RevitSharedResources2021/
|   |   |   |   `-- RevitSharedResources2021.csproj
|   |   |   |-- RevitSharedResources2022/
|   |   |   |   `-- RevitSharedResources2022.csproj
|   |   |   |-- RevitSharedResources2023/
|   |   |   |   `-- RevitSharedResources2023.csproj
|   |   |   |-- RevitSharedResources2024/
|   |   |   |   `-- RevitSharedResources2024.csproj
|   |   |   |-- RevitSharedResources2025/
|   |   |   |   `-- RevitSharedResources2025.csproj
|   |   |   |-- RevitSharedResources2026/
|   |   |   |   `-- RevitSharedResources2026.csproj
|   |   |   |-- Scripts/
|   |   |   |   |-- AutoClickSecurityDialog.cs
|   |   |   |   |-- AutoClickSecurityDialog.ps1
|   |   |   |   |-- BatchSendToSpeckle.ps1
|   |   |   |   |-- CheckSpeckleAccount.ps1
|   |   |   |   |-- ConnectRevitToAWS.md
|   |   |   |   |-- CreateAccountManually.cs
|   |   |   |   |-- DiagnoseAuthIssue.ps1
|   |   |   |   |-- FindAndSendWaddellSamples.ps1
|   |   |   |   |-- FixAccountToAWS.ps1
|   |   |   |   |-- FixOAuthTokenExchange.md
|   |   |   |   |-- INSTALL_OR_USE_UI.md
|   |   |   |   |-- ManuallyAddAccount.ps1
|   |   |   |   |-- OAUTH_FIX_SUMMARY.md
|   |   |   |   |-- README.md
|   |   |   |   |-- TestAWSAuth.ps1
|   |   |   |   `-- UpdateConfigToAWS.ps1
|   |   |   |-- ConnectorRevit.sln
|   |   |   |-- ConnectorRevit.slnf
|   |   |   |-- PROXY_MIGRATION_PLAN.md
|   |   |   |-- README.md
|   |   |   `-- REVIT_2026_SETUP.md
|   |   |-- ConnectorRhino/
|   |   |   |-- ConnectorRhino/
|   |   |   |   |-- ConnectorRhinoShared/
|   |   |   |   |   |-- Entry/
|   |   |   |   |   |   |-- Plugin.cs
|   |   |   |   |   |   |-- SpeckleCommandMac.cs
|   |   |   |   |   |   |-- SpeckleCommandWin.cs
|   |   |   |   |   |   |-- SpeckleMappingsCommandMac.cs
|   |   |   |   |   |   `-- SpeckleMappingsCommandWin.cs
|   |   |   |   |   |-- Resources/
|   |   |   |   |   |   |-- icon.ico
|   |   |   |   |   |   `-- mapper.ico
|   |   |   |   |   |-- UI/
|   |   |   |   |   |   |-- ConnectorBindingsRhino.3DView.cs
|   |   |   |   |   |   |-- ConnectorBindingsRhino.cs
|   |   |   |   |   |   |-- ConnectorBindingsRhino.Events.cs
|   |   |   |   |   |   |-- ConnectorBindingsRhino.Previews.cs
|   |   |   |   |   |   |-- ConnectorBindingsRhino.Receive.cs
|   |   |   |   |   |   |-- ConnectorBindingsRhino.Selection.cs
|   |   |   |   |   |   |-- ConnectorBindingsRhino.Send.cs
|   |   |   |   |   |   |-- ConnectorBindingsRhino.Settings.cs
|   |   |   |   |   |   |-- DuiPanel.xaml
|   |   |   |   |   |   |-- DuiPanel.xaml.cs
|   |   |   |   |   |   |-- MappingBindingsRhino.cs
|   |   |   |   |   |   |-- MappingsPanel.xaml
|   |   |   |   |   |   `-- MappingsPanel.xaml.cs
|   |   |   |   |   |-- ConnectorRhinoShared.projitems
|   |   |   |   |   |-- ConnectorRhinoShared.shproj
|   |   |   |   |   |-- MacOSHelpers.cs
|   |   |   |   |   |-- Resources.Designer.cs
|   |   |   |   |   |-- Resources.resx
|   |   |   |   |   `-- Utils.cs
|   |   |   |   `-- Toolbars/
|   |   |   |       `-- SpeckleConnectorRhino.rui
|   |   |   |-- ConnectorRhino6/
|   |   |   |   `-- ConnectorRhino6.csproj
|   |   |   |-- ConnectorRhino7/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorRhino7.csproj
|   |   |   |-- ConnectorRhino8/
|   |   |   |   `-- ConnectorRhino8.csproj
|   |   |   |-- ConnectorRhino.sln
|   |   |   |-- ConnectorRhino.slnf
|   |   |   `-- README.md
|   |   |-- ConnectorTeklaStructures/
|   |   |   |-- ConnectorTeklaStructures2020/
|   |   |   |   `-- ConnectorTeklaStructures2020.csproj
|   |   |   |-- ConnectorTeklaStructures2021/
|   |   |   |   `-- ConnectorTeklaStructures2021.csproj
|   |   |   |-- ConnectorTeklaStructures2022/
|   |   |   |   `-- ConnectorTeklaStructures2022.csproj
|   |   |   |-- ConnectorTeklaStructures2023/
|   |   |   |   |-- Properties/
|   |   |   |   |   `-- launchSettings.json
|   |   |   |   `-- ConnectorTeklaStructures2023.csproj
|   |   |   |-- ConnectorTeklaStructuresShared/
|   |   |   |   |-- StreamStateManager/
|   |   |   |   |   `-- StreamStateManager.cs
|   |   |   |   |-- UI/
|   |   |   |   |   |-- ConnectorBindingsTeklaStructure.Send.cs
|   |   |   |   |   |-- ConnectorBindingsTeklaStructure.Settings.cs
|   |   |   |   |   |-- ConnectorBindingsTeklaStructures.ClientOperations.cs
|   |   |   |   |   |-- ConnectorBindingsTeklaStructures.cs
|   |   |   |   |   |-- ConnectorBindingsTeklaStructures.Receive.cs
|   |   |   |   |   |-- ConnectorBindingsTeklaStructures.Recieve.cs
|   |   |   |   |   `-- ConnectorBindingsTeklaStructures.Selection.cs
|   |   |   |   |-- Util/
|   |   |   |   |   `-- ConnectorTeklaStructuresUtils.cs
|   |   |   |   |-- ConnectorTeklaStructuresShared.projitems
|   |   |   |   |-- ConnectorTeklaStructuresShared.shproj
|   |   |   |   |-- et_element_Speckle.ConnectorTeklaStructures_Legacy.bmp
|   |   |   |   |-- MainForm.cs
|   |   |   |   |-- MainForm.Designer.cs
|   |   |   |   |-- MainForm.resx
|   |   |   |   |-- MainPlugin.cs
|   |   |   |   `-- PolygonMesherReferencer.cs
|   |   |   |-- ConnectorTeklaStructures.sln
|   |   |   |-- ConnectorTeklaStructures.slnf
|   |   |   |-- Exclude.txt
|   |   |   `-- Manifest.xml
|   |   |-- Core/
|   |   |   |-- Core/
|   |   |   |   |-- Api/
|   |   |   |   |   |-- GraphQL/
|   |   |   |   |   |   |-- Enums/
|   |   |   |   |   |   |   |-- FileUploadConversionStatus.cs
|   |   |   |   |   |   |   |-- ProjectCommentsUpdatedMessageType.cs
|   |   |   |   |   |   |   |-- ProjectFileImportUpdatedMessageType.cs
|   |   |   |   |   |   |   |-- ProjectModelsUpdatedMessageType.cs
|   |   |   |   |   |   |   |-- ProjectPendingModelsUpdatedMessageType.cs
|   |   |   |   |   |   |   |-- ProjectUpdatedMessageType.cs
|   |   |   |   |   |   |   |-- ProjectVersionsUpdatedMessageType.cs
|   |   |   |   |   |   |   |-- ProjectVisibility.cs
|   |   |   |   |   |   |   |-- ResourceType.cs
|   |   |   |   |   |   |   `-- UserProjectsUpdatedMessageType.cs
|   |   |   |   |   |   |-- Inputs/
|   |   |   |   |   |   |   |-- ModelInputs.cs
|   |   |   |   |   |   |   |-- ProjectInputs.cs
|   |   |   |   |   |   |   |-- SubscriptionInputs.cs
|   |   |   |   |   |   |   |-- UserInputs.cs
|   |   |   |   |   |   |   `-- VersionInputs.cs
|   |   |   |   |   |   |-- Legacy/
|   |   |   |   |   |   |   |-- Client.GraphqlCleintOperations/
|   |   |   |   |   |   |   |   |-- Client.ActivityOperations.cs
|   |   |   |   |   |   |   |   |-- Client.BranchOperations.cs
|   |   |   |   |   |   |   |   |-- Client.CommentOperations.cs
|   |   |   |   |   |   |   |   |-- Client.CommitOperations.cs
|   |   |   |   |   |   |   |   |-- Client.ObjectOperations.cs
|   |   |   |   |   |   |   |   |-- Client.ServerOperations.cs
|   |   |   |   |   |   |   |   |-- Client.StreamOperations.cs
|   |   |   |   |   |   |   |   `-- Client.UserOperations.cs
|   |   |   |   |   |   |   |-- Client.Subscriptions/
|   |   |   |   |   |   |   |   |-- Client.Subscriptions.Branch.cs
|   |   |   |   |   |   |   |   |-- Client.Subscriptions.Commit.cs
|   |   |   |   |   |   |   |   `-- Client.Subscriptions.Stream.cs
|   |   |   |   |   |   |   |-- LegacyGraphQLModels.cs
|   |   |   |   |   |   |   |-- Manager.cs
|   |   |   |   |   |   |   `-- SubscriptionModels.cs
|   |   |   |   |   |   |-- Models/
|   |   |   |   |   |   |   |-- Responses/
|   |   |   |   |   |   |   |   |-- MutationResponses.cs
|   |   |   |   |   |   |   |   `-- Responses.cs
|   |   |   |   |   |   |   |-- Collections.cs
|   |   |   |   |   |   |   |-- Comment.cs
|   |   |   |   |   |   |   |-- FileUpload.cs
|   |   |   |   |   |   |   |-- Model.cs
|   |   |   |   |   |   |   |-- ModelExtensions.cs
|   |   |   |   |   |   |   |-- ModelsTreeItem.cs
|   |   |   |   |   |   |   |-- PendingStreamCollaborator.cs
|   |   |   |   |   |   |   |-- Project.cs
|   |   |   |   |   |   |   |-- ProjectCollaborator.cs
|   |   |   |   |   |   |   |-- ResourceIdentifier.cs
|   |   |   |   |   |   |   |-- ServerInfo.cs
|   |   |   |   |   |   |   |-- SubscriptionMessages.cs
|   |   |   |   |   |   |   |-- User.cs
|   |   |   |   |   |   |   |-- Version.cs
|   |   |   |   |   |   |   |-- ViewerResourceGroup.cs
|   |   |   |   |   |   |   |-- ViewerResourceItem.cs
|   |   |   |   |   |   |   `-- Workspace.cs
|   |   |   |   |   |   |-- Resources/
|   |   |   |   |   |   |   |-- ActiveUserResource.cs
|   |   |   |   |   |   |   |-- CommentResource.cs
|   |   |   |   |   |   |   |-- graphql.config.yml
|   |   |   |   |   |   |   |-- ModelResource.cs
|   |   |   |   |   |   |   |-- OtherUserResource.cs
|   |   |   |   |   |   |   |-- ProjectInviteResource.cs
|   |   |   |   |   |   |   |-- ProjectResource.cs
|   |   |   |   |   |   |   |-- SubscriptionResource.cs
|   |   |   |   |   |   |   |-- VersionResource.cs
|   |   |   |   |   |   |   `-- WorkspaceResource.cs
|   |   |   |   |   |   |-- Serializer/
|   |   |   |   |   |   |   |-- ConstantCaseEnumConverter.cs
|   |   |   |   |   |   |   |-- MapConverter.cs
|   |   |   |   |   |   |   `-- NewtonsoftJsonSerializer.cs
|   |   |   |   |   |   |-- .editorconfig
|   |   |   |   |   |   |-- Client.cs
|   |   |   |   |   |   |-- GraphQLHttpClientExtensions.cs
|   |   |   |   |   |   |-- ISpeckleGraphQLClient.cs
|   |   |   |   |   |   `-- StreamRoles.cs
|   |   |   |   |   |-- Operations/
|   |   |   |   |   |   |-- Operations.cs
|   |   |   |   |   |   |-- Operations.Receive.cs
|   |   |   |   |   |   |-- Operations.Receive.Obsolete.cs
|   |   |   |   |   |   |-- Operations.Send.cs
|   |   |   |   |   |   |-- Operations.Send.Obsolete.cs
|   |   |   |   |   |   `-- Operations.Serialize.cs
|   |   |   |   |   |-- Exceptions.cs
|   |   |   |   |   |-- Helpers.cs
|   |   |   |   |   `-- ServerLimits.cs
|   |   |   |   |-- Credentials/
|   |   |   |   |   |-- Account.cs
|   |   |   |   |   |-- AccountManager.cs
|   |   |   |   |   |-- Exceptions.cs
|   |   |   |   |   |-- graphql.config.yml
|   |   |   |   |   |-- Responses.cs
|   |   |   |   |   `-- StreamWrapper.cs
|   |   |   |   |-- Helpers/
|   |   |   |   |   |-- Constants.cs
|   |   |   |   |   |-- Crypt.cs
|   |   |   |   |   |-- Http.cs
|   |   |   |   |   |-- Open.cs
|   |   |   |   |   |-- Path.cs
|   |   |   |   |   `-- State.cs
|   |   |   |   |-- Kits/
|   |   |   |   |   |-- ConverterInterfaces/
|   |   |   |   |   |   `-- IFinalizable.cs
|   |   |   |   |   |-- Applications.cs
|   |   |   |   |   |-- Attributes.cs
|   |   |   |   |   |-- Exceptions.cs
|   |   |   |   |   |-- ISpeckleConverter.cs
|   |   |   |   |   |-- ISpeckleKit.cs
|   |   |   |   |   |-- KitDeclaration.cs
|   |   |   |   |   |-- KitManager.cs
|   |   |   |   |   `-- Units.cs
|   |   |   |   |-- Logging/
|   |   |   |   |   |-- Analytics.cs
|   |   |   |   |   |-- CumulativeTimer.cs
|   |   |   |   |   |-- ExceptionHelpers.cs
|   |   |   |   |   |-- LoggingHelpers.cs
|   |   |   |   |   |-- Setup.cs
|   |   |   |   |   |-- SpeckleException.cs
|   |   |   |   |   |-- SpeckleLog.cs
|   |   |   |   |   `-- SpeckleNonUserFacingException.cs
|   |   |   |   |-- Models/
|   |   |   |   |   |-- Extensions/
|   |   |   |   |   |   `-- BaseExtensions.cs
|   |   |   |   |   |-- GraphTraversal/
|   |   |   |   |   |   |-- DefaultTraversal.cs
|   |   |   |   |   |   |-- GraphTraversal.cs
|   |   |   |   |   |   |-- ITraversalRule.cs
|   |   |   |   |   |   |-- RuleBuilder.cs
|   |   |   |   |   |   |-- TraversalContextExtensions.cs
|   |   |   |   |   |   `-- TraversalContexts.cs
|   |   |   |   |   |-- ApplicationObject.cs
|   |   |   |   |   |-- Attributes.cs
|   |   |   |   |   |-- Base.cs
|   |   |   |   |   |-- Blob.cs
|   |   |   |   |   |-- Collection.cs
|   |   |   |   |   |-- CommitObjectBuilder.cs
|   |   |   |   |   |-- DynamicBase.cs
|   |   |   |   |   |-- DynamicBaseMemberType.cs
|   |   |   |   |   |-- Extras.cs
|   |   |   |   |   |-- InvalidPropNameException.cs
|   |   |   |   |   |-- NestingInstructions.cs
|   |   |   |   |   |-- ProjectPermissionChecks.cs
|   |   |   |   |   `-- Utilities.cs
|   |   |   |   |-- Serialisation/
|   |   |   |   |   |-- SerializationUtilities/
|   |   |   |   |   |   |-- BaseObjectSerializationUtilities.cs
|   |   |   |   |   |   |-- CallsiteCache.cs
|   |   |   |   |   |   |-- DeserializationWorkerThreads.cs
|   |   |   |   |   |   |-- OperationTask.cs
|   |   |   |   |   |   `-- ValueConverter.cs
|   |   |   |   |   |-- BaseObjectDeserializerV2.cs
|   |   |   |   |   |-- BaseObjectSerializer.cs
|   |   |   |   |   |-- BaseObjectSerializerV2.cs
|   |   |   |   |   `-- SpeckleSerializerException.cs
|   |   |   |   |-- Transports/
|   |   |   |   |   |-- ServerUtils/
|   |   |   |   |   |   |-- GzipContent.cs
|   |   |   |   |   |   |-- IServerApi.cs
|   |   |   |   |   |   |-- ParallelServerAPI.cs
|   |   |   |   |   |   `-- ServerAPI.cs
|   |   |   |   |   |-- Exceptions.cs
|   |   |   |   |   |-- ITransport.cs
|   |   |   |   |   |-- Memory.cs
|   |   |   |   |   |-- Server.cs
|   |   |   |   |   |-- ServerV2.cs
|   |   |   |   |   |-- SQLite.cs
|   |   |   |   |   |-- TransportHelpers.cs
|   |   |   |   |   `-- Utilities.cs
|   |   |   |   |-- Core.csproj
|   |   |   |   `-- SharpResources.cs
|   |   |   |-- notes/
|   |   |   |   `-- sqlite-performance.md
|   |   |   |-- Tests/
|   |   |   |   |-- Speckle.Core.Tests.Integration/
|   |   |   |   |   |-- Api/
|   |   |   |   |   |   `-- GraphQL/
|   |   |   |   |   |       |-- Legacy/
|   |   |   |   |   |       |   `-- LegacyAPITests.cs
|   |   |   |   |   |       `-- Resources/
|   |   |   |   |   |           |-- ActiveUserResourceTests.cs
|   |   |   |   |   |           |-- ModelResourceExceptionalTests.cs
|   |   |   |   |   |           |-- ModelResourceTests.cs
|   |   |   |   |   |           |-- OtherUserResourceTests.cs
|   |   |   |   |   |           |-- ProjectInviteResourceExceptionalTests.cs
|   |   |   |   |   |           |-- ProjectInviteResourceTests.cs
|   |   |   |   |   |           |-- ProjectResourceExceptionalTests.cs
|   |   |   |   |   |           |-- ProjectResourceTests.cs
|   |   |   |   |   |           |-- SubscriptionResourceTests.cs
|   |   |   |   |   |           `-- VersionResourceTests.cs
|   |   |   |   |   |-- Credentials/
|   |   |   |   |   |   `-- UserServerInfoTests.cs
|   |   |   |   |   |-- Fixtures.cs
|   |   |   |   |   |-- GraphQLCLient.cs
|   |   |   |   |   |-- ServerTransportTests.cs
|   |   |   |   |   |-- Speckle.Core.Tests.Integration.csproj
|   |   |   |   |   `-- Usings.cs
|   |   |   |   |-- Speckle.Core.Tests.Performance/
|   |   |   |   |   |-- Api/
|   |   |   |   |   |   `-- Operations/
|   |   |   |   |   |       |-- ReceiveFromSQLite.cs
|   |   |   |   |   |       `-- TraverseCommit.cs
|   |   |   |   |   |-- Serialisation/
|   |   |   |   |   |   `-- DeserializationWorkerThreads.cs
|   |   |   |   |   |-- Program.cs
|   |   |   |   |   |-- RegressionTestConfig.cs
|   |   |   |   |   |-- Speckle.Core.Tests.Performance.csproj
|   |   |   |   |   `-- TestDataHelper.cs
|   |   |   |   `-- Speckle.Core.Tests.Unit/
|   |   |   |       |-- Api/
|   |   |   |       |   |-- Operations/
|   |   |   |       |   |   |-- ClosureTests.cs
|   |   |   |       |   |   |-- OperationsReceiveTests.cs
|   |   |   |       |   |   |-- OperationsReceiveTests.Exceptional.cs
|   |   |   |       |   |   |-- SendReceiveLocal.cs
|   |   |   |       |   |   `-- SerializationTests.cs
|   |   |   |       |   |-- GraphQLClient.cs
|   |   |   |       |   `-- HelpersTests.cs
|   |   |   |       |-- Credentials/
|   |   |   |       |   |-- Accounts.cs
|   |   |   |       |   |-- AccountServerMigrationTests.cs
|   |   |   |       |   |-- FE2WrapperTests.cs
|   |   |   |       |   `-- StreamWrapperTests.cs
|   |   |   |       |-- Helpers/
|   |   |   |       |   `-- Path.cs
|   |   |   |       |-- Kits/
|   |   |   |       |   |-- KitManagerTests.cs
|   |   |   |       |   |-- TestKit.cs
|   |   |   |       |   `-- UnitsTest.cs
|   |   |   |       |-- Logging/
|   |   |   |       |   `-- SpeckleLogTests.cs
|   |   |   |       |-- Models/
|   |   |   |       |   |-- Extensions/
|   |   |   |       |   |   |-- BaseExtensionsTests.cs
|   |   |   |       |   |   |-- DisplayValueTests.cs
|   |   |   |       |   |   `-- ExceptionTests.cs
|   |   |   |       |   |-- GraphTraversal/
|   |   |   |       |   |   |-- GraphTraversalTests.cs
|   |   |   |       |   |   `-- TraversalMockObjects.cs
|   |   |   |       |   |-- BaseTests.cs
|   |   |   |       |   |-- Hashing.cs
|   |   |   |       |   |-- SpeckleType.cs
|   |   |   |       |   |-- TraversalTests.cs
|   |   |   |       |   `-- UtilitiesTests.cs
|   |   |   |       |-- Serialisation/
|   |   |   |       |   |-- ObjectModelDeprecationTests.cs
|   |   |   |       |   |-- SerializerBreakingChanges.cs
|   |   |   |       |   `-- SerializerNonBreakingChanges.cs
|   |   |   |       |-- Transports/
|   |   |   |       |   |-- DiskTransportTests.cs
|   |   |   |       |   |-- MemoryTransportTests.cs
|   |   |   |       |   |-- SQLiteTransportTests.cs
|   |   |   |       |   `-- TransportTests.cs
|   |   |   |       |-- Fixtures.cs
|   |   |   |       `-- Speckle.Core.Tests.Unit.csproj
|   |   |   |-- Transports/
|   |   |   |   |-- DiskTransport/
|   |   |   |   |   |-- DiskTransport.cs
|   |   |   |   |   `-- DiskTransport.csproj
|   |   |   |   `-- MongoDBTransport/
|   |   |   |       |-- MongoDB.cs
|   |   |   |       `-- MongoDBTransport.csproj
|   |   |   |-- CONTRIBUTING.md
|   |   |   |-- Core.sln
|   |   |   |-- docker-compose.yml
|   |   |   |-- ISSUE_TEMPLATE.md
|   |   |   |-- LICENSE
|   |   |   `-- README.md
|   |   |-- DesktopUI2/
|   |   |   |-- AvaloniaHwndHost/
|   |   |   |   |-- AvaloniaHwndHost.cs
|   |   |   |   |-- AvaloniaHwndHost.csproj
|   |   |   |   `-- UnmanagedMethods.cs
|   |   |   |-- DesktopUI2/
|   |   |   |   |-- Assets/
|   |   |   |   |   |-- icon.ico
|   |   |   |   |   |-- instructions.gif
|   |   |   |   |   `-- SpaceGrotesk-VariableFont_wght.ttf
|   |   |   |   |-- Models/
|   |   |   |   |   |-- Filters/
|   |   |   |   |   |   |-- AllSelectionFilter.cs
|   |   |   |   |   |   |-- ISelectionFilter.cs
|   |   |   |   |   |   |-- ListSelectionFilter.cs
|   |   |   |   |   |   |-- ManualSelectionFilter.cs
|   |   |   |   |   |   |-- PropertySelectionFilter.cs
|   |   |   |   |   |   |-- SelectionFilterConverter.cs
|   |   |   |   |   |   `-- TreeSelectionFilter.cs
|   |   |   |   |   |-- Scheduler/
|   |   |   |   |   |   `-- Trigger.cs
|   |   |   |   |   |-- Settings/
|   |   |   |   |   |   |-- CheckBoxSetting.cs
|   |   |   |   |   |   |-- ISetting.cs
|   |   |   |   |   |   |-- ListBoxSetting.cs
|   |   |   |   |   |   |-- MappingSeting.cs
|   |   |   |   |   |   |-- MultiSelectBoxSetting.cs
|   |   |   |   |   |   |-- NumericSetting.cs
|   |   |   |   |   |   |-- SettingsConverter.cs
|   |   |   |   |   |   `-- TextBoxSetting.cs
|   |   |   |   |   |-- TypeMappingOnReceive/
|   |   |   |   |   |   |-- HostType.cs
|   |   |   |   |   |   |-- IHostTypeContainer.cs
|   |   |   |   |   |   |-- ISingleHostType.cs
|   |   |   |   |   |   |-- ISingleValueToMap.cs
|   |   |   |   |   |   |-- ITypeMap.cs
|   |   |   |   |   |   `-- MappingValue.cs
|   |   |   |   |   |-- ConfigManager.cs
|   |   |   |   |   |-- MenuItem.cs
|   |   |   |   |   |-- NotificationManager.cs
|   |   |   |   |   |-- StreamAccountWrapper.cs
|   |   |   |   |   `-- StreamState.cs
|   |   |   |   |-- Native/
|   |   |   |   |   `-- libAvalonia.Native.OSX.dylib
|   |   |   |   |-- Styles/
|   |   |   |   |   |-- Button.xaml
|   |   |   |   |   |-- ChipListBox.xaml
|   |   |   |   |   |-- ComboBox.xaml
|   |   |   |   |   |-- Dialog.xaml
|   |   |   |   |   |-- Expander.xaml
|   |   |   |   |   |-- FloatingButton.xaml
|   |   |   |   |   |-- ListBox.xaml
|   |   |   |   |   |-- MenuItem.xaml
|   |   |   |   |   |-- NotificationCard.xaml
|   |   |   |   |   |-- NotificationManager.xaml
|   |   |   |   |   |-- Playground.xaml
|   |   |   |   |   |-- Styles.xaml
|   |   |   |   |   |-- Text.xaml
|   |   |   |   |   `-- TextBox.xaml
|   |   |   |   |-- ViewModels/
|   |   |   |   |   |-- DesignViewModels/
|   |   |   |   |   |   |-- DesignHomeViewModel.cs
|   |   |   |   |   |   |-- DesignNotificationsViewModel.cs
|   |   |   |   |   |   |-- DesignReportViewModel.cs
|   |   |   |   |   |   |-- DesignSavedStreamsViewModel.cs
|   |   |   |   |   |   `-- DesignShareViewModel.cs
|   |   |   |   |   |-- MappingTool/
|   |   |   |   |   |   |-- MappingsViewModel.cs
|   |   |   |   |   |   `-- Schemas.cs
|   |   |   |   |   |-- AccountViewModel.cs
|   |   |   |   |   |-- ActivityViewModel.cs
|   |   |   |   |   |-- ApplicationObjectViewModel.cs
|   |   |   |   |   |-- BranchViewModel.cs
|   |   |   |   |   |-- CollaboratorsViewModel.cs
|   |   |   |   |   |-- CommentViewModel.cs
|   |   |   |   |   |-- DialogViewModel.cs
|   |   |   |   |   |-- FilterViewModel.cs
|   |   |   |   |   |-- HomeViewModel.cs
|   |   |   |   |   |-- ImportFamiliesDialogViewModel.cs
|   |   |   |   |   |-- LogInViewModel.cs
|   |   |   |   |   |-- MainViewModel.cs
|   |   |   |   |   |-- MenuItemViewModel.cs
|   |   |   |   |   |-- NotificationsViewModel.cs
|   |   |   |   |   |-- NotificationViewModel.cs
|   |   |   |   |   |-- OneClickViewModel.cs
|   |   |   |   |   |-- PopUpNotificationViewModel.cs
|   |   |   |   |   |-- ProgressViewModel.cs
|   |   |   |   |   |-- SchedulerViewModel.cs
|   |   |   |   |   |-- SettingsPageViewModel.cs
|   |   |   |   |   |-- SettingViewModel.cs
|   |   |   |   |   |-- StreamSelectorViewModel.cs
|   |   |   |   |   |-- StreamViewModel.cs
|   |   |   |   |   |-- TypeMappingOnReceiveViewModel.cs
|   |   |   |   |   |-- ViewModelBase.cs
|   |   |   |   |   `-- WorkspaceViewModel.cs
|   |   |   |   |-- Views/
|   |   |   |   |   |-- AttachedProperties/
|   |   |   |   |   |   `-- BlockSelection.cs
|   |   |   |   |   |-- Controls/
|   |   |   |   |   |   |-- StreamEditControls/
|   |   |   |   |   |   |   |-- Activity.xaml
|   |   |   |   |   |   |   |-- Activity.xaml.cs
|   |   |   |   |   |   |   |-- Comments.xaml
|   |   |   |   |   |   |   |-- Comments.xaml.cs
|   |   |   |   |   |   |   |-- Receive.xaml
|   |   |   |   |   |   |   |-- Receive.xaml.cs
|   |   |   |   |   |   |   |-- Report.xaml
|   |   |   |   |   |   |   |-- Report.xaml.cs
|   |   |   |   |   |   |   |-- Send.xaml
|   |   |   |   |   |   |   `-- Send.xaml.cs
|   |   |   |   |   |   |-- CollaboratorsControl.xaml
|   |   |   |   |   |   |-- CollaboratorsControl.xaml.cs
|   |   |   |   |   |   |-- PreviewButton.xaml
|   |   |   |   |   |   |-- PreviewButton.xaml.cs
|   |   |   |   |   |   |-- SavedStreams.xaml
|   |   |   |   |   |   |-- SavedStreams.xaml.cs
|   |   |   |   |   |   |-- StreamDetails.xaml
|   |   |   |   |   |   |-- StreamDetails.xaml.cs
|   |   |   |   |   |   |-- StreamSelector.xaml
|   |   |   |   |   |   `-- StreamSelector.xaml.cs
|   |   |   |   |   |-- Converters/
|   |   |   |   |   |   |-- EmptyFalseValueConverter.cs
|   |   |   |   |   |   |-- EnumBooleanConverter.cs
|   |   |   |   |   |   |-- OpacityDoubleConverter.cs
|   |   |   |   |   |   |-- OpacityValueConverter.cs
|   |   |   |   |   |   |-- RoleCannotShareValueConverter.cs
|   |   |   |   |   |   |-- RoleCanReceiveValueConverter.cs
|   |   |   |   |   |   |-- RoleCanSendValueConverter.cs
|   |   |   |   |   |   |-- RoleCanShareValueConverter.cs
|   |   |   |   |   |   |-- RoleValueConverter.cs
|   |   |   |   |   |   |-- StreamEditHeightConverter.cs
|   |   |   |   |   |   |-- StringEqualsConverter.cs
|   |   |   |   |   |   `-- StringOpacityValueConverter.cs
|   |   |   |   |   |-- DataTemplates/
|   |   |   |   |   |   |-- FilterTemplateSelector.cs
|   |   |   |   |   |   `-- SettingsTemplateSelector.cs
|   |   |   |   |   |-- Filters/
|   |   |   |   |   |   |-- AllFilterView.xaml
|   |   |   |   |   |   |-- AllFilterView.xaml.cs
|   |   |   |   |   |   |-- ListFilterView.xaml
|   |   |   |   |   |   |-- ListFilterView.xaml.cs
|   |   |   |   |   |   |-- ManualFilterView.xaml
|   |   |   |   |   |   |-- ManualFilterView.xaml.cs
|   |   |   |   |   |   |-- PropertyFilterView.xaml
|   |   |   |   |   |   |-- PropertyFilterView.xaml.cs
|   |   |   |   |   |   |-- TreeFilterView.xaml
|   |   |   |   |   |   `-- TreeFilterView.xaml.cs
|   |   |   |   |   |-- Mappings/
|   |   |   |   |   |   `-- Controls/
|   |   |   |   |   |       |-- RevitBasic.xaml
|   |   |   |   |   |       |-- RevitBasic.xaml.cs
|   |   |   |   |   |       |-- RevitMEP.xaml
|   |   |   |   |   |       `-- RevitMEP.xaml.cs
|   |   |   |   |   |-- Pages/
|   |   |   |   |   |   |-- CollaboratorsView.xaml
|   |   |   |   |   |   |-- CollaboratorsView.xaml.cs
|   |   |   |   |   |   |-- HomeView.xaml
|   |   |   |   |   |   |-- HomeView.xaml.cs
|   |   |   |   |   |   |-- LogInView.xaml
|   |   |   |   |   |   |-- LogInView.xaml.cs
|   |   |   |   |   |   |-- NotificationsView.xaml
|   |   |   |   |   |   |-- NotificationsView.xaml.cs
|   |   |   |   |   |   |-- OneClickView.xaml
|   |   |   |   |   |   |-- OneClickView.xaml.cs
|   |   |   |   |   |   |-- SettingsView.xaml
|   |   |   |   |   |   |-- SettingsView.xaml.cs
|   |   |   |   |   |   |-- StreamEditView.xaml
|   |   |   |   |   |   `-- StreamEditView.xaml.cs
|   |   |   |   |   |-- Settings/
|   |   |   |   |   |   |-- CheckBoxSettingView.xaml
|   |   |   |   |   |   |-- CheckBoxSettingView.xaml.cs
|   |   |   |   |   |   |-- ListBoxSettingView.xaml
|   |   |   |   |   |   |-- ListBoxSettingView.xaml.cs
|   |   |   |   |   |   |-- MultiSelectBoxSettingView.xaml
|   |   |   |   |   |   |-- MultiSelectBoxSettingView.xaml.cs
|   |   |   |   |   |   |-- NumericSettingView.xaml
|   |   |   |   |   |   |-- NumericSettingView.xaml.cs
|   |   |   |   |   |   |-- TextBoxSettingView.xaml
|   |   |   |   |   |   `-- TextBoxSettingView.xaml.cs
|   |   |   |   |   |-- Windows/
|   |   |   |   |   |   `-- Dialogs/
|   |   |   |   |   |       |-- AddAccountDialog.xaml
|   |   |   |   |   |       |-- AddAccountDialog.xaml.cs
|   |   |   |   |   |       |-- AddFromUrlDialog.xaml
|   |   |   |   |   |       |-- AddFromUrlDialog.xaml.cs
|   |   |   |   |   |       |-- ChangeRoleDialog.xaml
|   |   |   |   |   |       |-- ChangeRoleDialog.xaml.cs
|   |   |   |   |   |       |-- Dialog.xaml
|   |   |   |   |   |       |-- Dialog.xaml.cs
|   |   |   |   |   |       |-- DialogUserControl.cs
|   |   |   |   |   |       |-- IDialog.cs
|   |   |   |   |   |       |-- ImportExportAlert.xaml
|   |   |   |   |   |       |-- ImportExportAlert.xaml.cs
|   |   |   |   |   |       |-- ImportFamiliesDialog.xaml
|   |   |   |   |   |       |-- ImportFamiliesDialog.xaml.cs
|   |   |   |   |   |       |-- MappingViewDialog.xaml
|   |   |   |   |   |       |-- MappingViewDialog.xaml.cs
|   |   |   |   |   |       |-- MissingIncomingTypesDialog.xaml
|   |   |   |   |   |       |-- MissingIncomingTypesDialog.xaml.cs
|   |   |   |   |   |       |-- NewBranchDialog.xaml
|   |   |   |   |   |       |-- NewBranchDialog.xaml.cs
|   |   |   |   |   |       |-- NewStreamDialog.xaml
|   |   |   |   |   |       |-- NewStreamDialog.xaml.cs
|   |   |   |   |   |       |-- QuickOpsDialog.xaml
|   |   |   |   |   |       `-- QuickOpsDialog.xaml.cs
|   |   |   |   |   |-- MainUserControl.xaml
|   |   |   |   |   |-- MainUserControl.xaml.cs
|   |   |   |   |   |-- MainWindow.xaml
|   |   |   |   |   |-- MainWindow.xaml.cs
|   |   |   |   |   |-- MappingsControl.xaml
|   |   |   |   |   |-- MappingsControl.xaml.cs
|   |   |   |   |   |-- MappingsWindow.xaml
|   |   |   |   |   |-- MappingsWindow.xaml.cs
|   |   |   |   |   |-- Scheduler.xaml
|   |   |   |   |   `-- Scheduler.xaml.cs
|   |   |   |   |-- App.xaml
|   |   |   |   |-- App.xaml.cs
|   |   |   |   |-- ConnectorBindings.cs
|   |   |   |   |-- ConnectorHelpers.cs
|   |   |   |   |-- DesktopUI2.csproj
|   |   |   |   |-- DummyBindings.cs
|   |   |   |   |-- DummyMappingsBindings.cs
|   |   |   |   |-- MappingsBindings.cs
|   |   |   |   |-- Utils.cs
|   |   |   |   `-- ViewLocator.cs
|   |   |   |-- DesktopUI2.Launcher/
|   |   |   |   |-- DesktopUI2.Launcher.csproj
|   |   |   |   `-- Program.cs
|   |   |   |-- DesktopUI2.WPF/
|   |   |   |   |-- App.xaml
|   |   |   |   |-- App.xaml.cs
|   |   |   |   |-- AssemblyInfo.cs
|   |   |   |   |-- DesktopUI2.WPF.csproj
|   |   |   |   |-- MainWindow.xaml
|   |   |   |   `-- MainWindow.xaml.cs
|   |   |   |-- DesktopUI2.sln
|   |   |   `-- README.md
|   |   |-- Objects/
|   |   |   |-- Converters/
|   |   |   |   |-- ConverterAutocadCivil/
|   |   |   |   |   |-- ConverterAdvanceSteel2023/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterAdvanceSteel2023.csproj
|   |   |   |   |   |-- ConverterAdvanceSteel2024/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterAdvanceSteel2024.csproj
|   |   |   |   |   |-- ConverterAutocad2021/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterAutocad2021.csproj
|   |   |   |   |   |-- ConverterAutocad2022/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterAutocad2022.csproj
|   |   |   |   |   |-- ConverterAutocad2023/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterAutocad2023.csproj
|   |   |   |   |   |-- ConverterAutocad2024/
|   |   |   |   |   |   `-- ConverterAutocad2024.csproj
|   |   |   |   |   |-- ConverterAutocad2025/
|   |   |   |   |   |   `-- ConverterAutocad2025.csproj
|   |   |   |   |   |-- ConverterAutocadCivilShared/
|   |   |   |   |   |   |-- AdvanceSteel/
|   |   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   |   |-- PropertySets/
|   |   |   |   |   |   |   |   |   |-- AtomicElementProperties.cs
|   |   |   |   |   |   |   |   |   |-- BeamProperties.cs
|   |   |   |   |   |   |   |   |   |-- BoltPatternProperties.cs
|   |   |   |   |   |   |   |   |   |-- ConstructionElementProperties.cs
|   |   |   |   |   |   |   |   |   |-- FilerObjectProperties.cs
|   |   |   |   |   |   |   |   |   |-- MainAliasProperties.cs
|   |   |   |   |   |   |   |   |   |-- PolybeamProperties.cs
|   |   |   |   |   |   |   |   |   `-- ScrewBoltPatternProperties.cs
|   |   |   |   |   |   |   |   |-- ASBaseProperties.cs
|   |   |   |   |   |   |   |   |-- ASPropertiesCache.cs
|   |   |   |   |   |   |   |   |-- ASProperty.cs
|   |   |   |   |   |   |   |   |-- ASPropertyMethods.cs
|   |   |   |   |   |   |   |   |-- ASTypeData.cs
|   |   |   |   |   |   |   |   |-- IASProperties.cs
|   |   |   |   |   |   |   |   `-- StructureUtils.cs
|   |   |   |   |   |   |   |-- ConverterAutocadCivil.AdvanceSteel.cs
|   |   |   |   |   |   |   |-- ConverterAutocadCivil.ASGeometry.cs
|   |   |   |   |   |   |   |-- ConverterAutocadCivil.Beams.cs
|   |   |   |   |   |   |   |-- ConverterAutocadCivil.Bolts.cs
|   |   |   |   |   |   |   |-- ConverterAutocadCivil.DxfNames.cs
|   |   |   |   |   |   |   |-- ConverterAutocadCivil.Gratings.cs
|   |   |   |   |   |   |   |-- ConverterAutocadCivil.Plates.cs
|   |   |   |   |   |   |   |-- ConverterAutocadCivil.Slabs.cs
|   |   |   |   |   |   |   `-- ConverterAutocadCivil.SpecialParts.cs
|   |   |   |   |   |   |-- Converter.AutocadCivil.Utils.cs
|   |   |   |   |   |   |-- ConverterAutocadCivil.Civil.cs
|   |   |   |   |   |   |-- ConverterAutocadCivil.cs
|   |   |   |   |   |   |-- ConverterAutocadCivil.Geometry.cs
|   |   |   |   |   |   |-- ConverterAutocadCivil.Other.cs
|   |   |   |   |   |   |-- ConverterAutocadCivilShared.projitems
|   |   |   |   |   |   `-- ConverterAutocadCivilShared.shproj
|   |   |   |   |   |-- ConverterCivil2021/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterCivil2021.csproj
|   |   |   |   |   |-- ConverterCivil2022/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterCivil2022.csproj
|   |   |   |   |   |-- ConverterCivil2023/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterCivil2023.csproj
|   |   |   |   |   |-- ConverterCivil2024/
|   |   |   |   |   |   `-- ConverterCivil2024.csproj
|   |   |   |   |   `-- ConverterCivil2025/
|   |   |   |   |       `-- ConverterCivil2025.csproj
|   |   |   |   |-- ConverterBentley/
|   |   |   |   |   |-- ConverterBentleyShared/
|   |   |   |   |   |   |-- ConverterBentley.Civil.cs
|   |   |   |   |   |   |-- ConverterBentley.cs
|   |   |   |   |   |   |-- ConverterBentley.Geometry.cs
|   |   |   |   |   |   |-- ConverterBentley.GridSystems.cs
|   |   |   |   |   |   |-- ConverterBentley.Utils.cs
|   |   |   |   |   |   |-- ConverterBentleyShared.projitems
|   |   |   |   |   |   `-- ConverterBentleyShared.shproj
|   |   |   |   |   |-- ConverterMicroStation/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterMicroStation.csproj
|   |   |   |   |   |-- ConverterOpenBuildings/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterOpenBuildings.csproj
|   |   |   |   |   |-- ConverterOpenRail/
|   |   |   |   |   |   `-- ConverterOpenRail.csproj
|   |   |   |   |   `-- ConverterOpenRoads/
|   |   |   |   |       |-- Properties/
|   |   |   |   |       |   `-- launchSettings.json
|   |   |   |   |       `-- ConverterOpenRoads.csproj
|   |   |   |   |-- ConverterCSI/
|   |   |   |   |   |-- ConverterCSIBridge/
|   |   |   |   |   |   `-- ConverterCSIBridge.csproj
|   |   |   |   |   |-- ConverterCSIShared/
|   |   |   |   |   |   |-- Extensions/
|   |   |   |   |   |   |   |-- ArcExtensions.cs
|   |   |   |   |   |   |   |-- CurveExtensions.cs
|   |   |   |   |   |   |   |-- ICurveExtensions.cs
|   |   |   |   |   |   |   |-- LineExtensions.cs
|   |   |   |   |   |   |   `-- PolycurveExtensions.cs
|   |   |   |   |   |   |-- Models/
|   |   |   |   |   |   |   |-- ApiResultValidator.cs
|   |   |   |   |   |   |   |-- DatabaseTableWrapper.cs
|   |   |   |   |   |   |   |-- Element1DAnalyticalResultConverter.cs
|   |   |   |   |   |   |   |-- Element2DAnalyticalResultConverter.cs
|   |   |   |   |   |   |   |-- ETABSGridLineDefinitionTable.cs
|   |   |   |   |   |   |   |-- NodeAnalyticalResultsConverter.cs
|   |   |   |   |   |   |   `-- ResultsConverter.cs
|   |   |   |   |   |   |-- PartialClasses/
|   |   |   |   |   |   |   |-- Analysis/
|   |   |   |   |   |   |   |   |-- ConvertModel.cs
|   |   |   |   |   |   |   |   |-- ConvertModelInfo.cs
|   |   |   |   |   |   |   |   |-- ConvertModelSettings.cs
|   |   |   |   |   |   |   |   `-- ConvertModelUnits.cs
|   |   |   |   |   |   |   |-- Geometry/
|   |   |   |   |   |   |   |   |-- ConvertArea.cs
|   |   |   |   |   |   |   |   |-- ConvertBeam.cs
|   |   |   |   |   |   |   |   |-- ConvertBraces.cs
|   |   |   |   |   |   |   |   |-- ConvertBuiltElement.cs
|   |   |   |   |   |   |   |   |-- ConvertColumn.cs
|   |   |   |   |   |   |   |   |-- ConvertFloor.cs
|   |   |   |   |   |   |   |   |-- ConvertFrame.cs
|   |   |   |   |   |   |   |   |-- ConvertGridLines.cs
|   |   |   |   |   |   |   |   |-- ConvertLine.cs
|   |   |   |   |   |   |   |   |-- ConvertLinks.cs
|   |   |   |   |   |   |   |   |-- ConvertPier.cs
|   |   |   |   |   |   |   |   |-- ConvertPoint.cs
|   |   |   |   |   |   |   |   |-- ConvertSpandrel.cs
|   |   |   |   |   |   |   |   |-- ConvertStories.cs
|   |   |   |   |   |   |   |   |-- ConvertTendon.cs
|   |   |   |   |   |   |   |   `-- ConvertWall.cs
|   |   |   |   |   |   |   |-- Loading/
|   |   |   |   |   |   |   |   |-- ConvertLoadCombination.cs
|   |   |   |   |   |   |   |   |-- ConvertLoadPattern.cs
|   |   |   |   |   |   |   |   |-- Loading1DElements.cs
|   |   |   |   |   |   |   |   |-- Loading2DElements.cs
|   |   |   |   |   |   |   |   `-- LoadingNode.cs
|   |   |   |   |   |   |   |-- Materials/
|   |   |   |   |   |   |   |   `-- ConvertMaterials.cs
|   |   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   |   |-- Convert1DProperty.cs
|   |   |   |   |   |   |   |   |-- Convert2DProperty.cs
|   |   |   |   |   |   |   |   |-- Convert2DPropertyFloor.cs
|   |   |   |   |   |   |   |   |-- Convert2DPropertyWall.cs
|   |   |   |   |   |   |   |   |-- ConvertDiaphragm.cs
|   |   |   |   |   |   |   |   |-- ConvertLinkProperty.cs
|   |   |   |   |   |   |   |   |-- ConvertSectionProfile.cs
|   |   |   |   |   |   |   |   |-- ConvertSpring.cs
|   |   |   |   |   |   |   |   `-- ConvertTendonProperty.cs
|   |   |   |   |   |   |   `-- Results/
|   |   |   |   |   |   |       |-- ConvertResultGlobal.cs
|   |   |   |   |   |   |       `-- ConvertResults.cs
|   |   |   |   |   |   |-- Services/
|   |   |   |   |   |   |   `-- ToNativeScalingService.cs
|   |   |   |   |   |   |-- AnalysisResultUtils.cs
|   |   |   |   |   |   |-- Constants.cs
|   |   |   |   |   |   |-- ConverterCSI.cs
|   |   |   |   |   |   |-- ConverterCSI.DatabaseTableUtils.cs
|   |   |   |   |   |   |-- ConverterCSIShared.projitems
|   |   |   |   |   |   |-- ConverterCSIShared.shproj
|   |   |   |   |   |   `-- ConverterCSIUtils.cs
|   |   |   |   |   |-- ConverterETABS/
|   |   |   |   |   |   `-- ConverterETABS.csproj
|   |   |   |   |   |-- ConverterSAFE/
|   |   |   |   |   |   `-- ConverterSAFE.csproj
|   |   |   |   |   `-- ConverterSAP2000/
|   |   |   |   |       `-- ConverterSAP2000.csproj
|   |   |   |   |-- ConverterDxf/
|   |   |   |   |   |-- ConverterDxf/
|   |   |   |   |   |   |-- ConverterDxf.csproj
|   |   |   |   |   |   |-- ConverterDxfSettings.cs
|   |   |   |   |   |   |-- SpeckleDxfConverter.cs
|   |   |   |   |   |   |-- SpeckleDxfConverter.Document.cs
|   |   |   |   |   |   |-- SpeckleDxfConverter.Geometry.cs
|   |   |   |   |   |   |-- SpeckleDxfConverter.Settings.cs
|   |   |   |   |   |   |-- SpeckleDxfConverter.Units.cs
|   |   |   |   |   |   `-- Utilities.cs
|   |   |   |   |   |-- ConverterDxf.Tests/
|   |   |   |   |   |   |-- Geometry/
|   |   |   |   |   |   |   |-- BrepTests.cs
|   |   |   |   |   |   |   |-- CurveTests.cs
|   |   |   |   |   |   |   |-- MeshTests.cs
|   |   |   |   |   |   |   `-- VectorTests.cs
|   |   |   |   |   |   |-- ConverterDxf.Tests.csproj
|   |   |   |   |   |   |-- ConverterFixture.cs
|   |   |   |   |   |   `-- ConverterSetup.cs
|   |   |   |   |   `-- ConverterDxf.sln
|   |   |   |   |-- ConverterDynamo/
|   |   |   |   |   |-- ConverterDynamoRevit/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterDynamoRevit.csproj
|   |   |   |   |   |-- ConverterDynamoRevit2021/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterDynamoRevit2021.csproj
|   |   |   |   |   |-- ConverterDynamoRevit2022/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterDynamoRevit2022.csproj
|   |   |   |   |   |-- ConverterDynamoRevit2023/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterDynamoRevit2023.csproj
|   |   |   |   |   |-- ConverterDynamoRevit2024/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterDynamoRevit2024.csproj
|   |   |   |   |   |-- ConverterDynamoSandbox/
|   |   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |   `-- launchSettings.json
|   |   |   |   |   |   `-- ConverterDynamoSandbox.csproj
|   |   |   |   |   |-- ConverterDynamoShared/
|   |   |   |   |   |   |-- ConverterDynamo.cs
|   |   |   |   |   |   |-- ConverterDynamo.Geometry.cs
|   |   |   |   |   |   |-- ConverterDynamo.Units.cs
|   |   |   |   |   |   |-- ConverterDynamo.Units.Revit.cs
|   |   |   |   |   |   |-- ConverterDynamoShared.projitems
|   |   |   |   |   |   |-- ConverterDynamoShared.shproj
|   |   |   |   |   |   `-- Utils.cs
|   |   |   |   |   |-- .gitignore
|   |   |   |   |   `-- LICENSE
|   |   |   |   |-- ConverterNavisworks/
|   |   |   |   |   |-- ConverterNavisworks/
|   |   |   |   |   |   |-- ConverterNavisworks.cs
|   |   |   |   |   |   |-- ConverterNavisworks.Geometry.cs
|   |   |   |   |   |   |-- ConverterNavisworks.Other.cs
|   |   |   |   |   |   |-- ConverterNavisworks.Properties.cs
|   |   |   |   |   |   |-- ConverterNavisworks.Settings.cs
|   |   |   |   |   |   |-- ConverterNavisworks.shproj
|   |   |   |   |   |   |-- ConverterNavisworks.ToNative.cs
|   |   |   |   |   |   |-- ConverterNavisworks.ToSpeckle.cs
|   |   |   |   |   |   |-- ConverterNavisworks.Types.cs
|   |   |   |   |   |   |-- ConverterNavisworks.Utilities.cs
|   |   |   |   |   |   `-- ConverterNavisworksShared.projitems
|   |   |   |   |   |-- ConverterNavisworks2020/
|   |   |   |   |   |   `-- ConverterNavisworks2020.csproj
|   |   |   |   |   |-- ConverterNavisworks2021/
|   |   |   |   |   |   `-- ConverterNavisworks2021.csproj
|   |   |   |   |   |-- ConverterNavisworks2022/
|   |   |   |   |   |   `-- ConverterNavisworks2022.csproj
|   |   |   |   |   |-- ConverterNavisworks2023/
|   |   |   |   |   |   `-- ConverterNavisworks2023.csproj
|   |   |   |   |   |-- ConverterNavisworks2024/
|   |   |   |   |   |   `-- ConverterNavisworks2024.csproj
|   |   |   |   |   `-- ConverterNavisworks2025/
|   |   |   |   |       `-- ConverterNavisworks2025.csproj
|   |   |   |   |-- ConverterRevit/
|   |   |   |   |   |-- ConverterRevit2020/
|   |   |   |   |   |   `-- ConverterRevit2020.csproj
|   |   |   |   |   |-- ConverterRevit2021/
|   |   |   |   |   |   |-- ConverterRevit2021.csproj
|   |   |   |   |   |   `-- RevitClassDiagram.cd
|   |   |   |   |   |-- ConverterRevit2022/
|   |   |   |   |   |   `-- ConverterRevit2022.csproj
|   |   |   |   |   |-- ConverterRevit2023/
|   |   |   |   |   |   `-- ConverterRevit2023.csproj
|   |   |   |   |   |-- ConverterRevit2024/
|   |   |   |   |   |   `-- ConverterRevit2024.csproj
|   |   |   |   |   |-- ConverterRevit2025/
|   |   |   |   |   |   `-- ConverterRevit2025.csproj
|   |   |   |   |   |-- ConverterRevit2026/
|   |   |   |   |   |   `-- ConverterRevit2026.csproj
|   |   |   |   |   |-- ConverterRevitShared/
|   |   |   |   |   |   |-- Extensions/
|   |   |   |   |   |   |   |-- CategoryExtensions.cs
|   |   |   |   |   |   |   |-- ConnectorExtensions.cs
|   |   |   |   |   |   |   |-- DefinitionExtensions.cs
|   |   |   |   |   |   |   |-- DisplayUnitTypeExtensions.cs
|   |   |   |   |   |   |   |-- ElementExtensions.cs
|   |   |   |   |   |   |   |-- ForgeTypeIdExtensions.cs
|   |   |   |   |   |   |   |-- ParameterExtensions.cs
|   |   |   |   |   |   |   `-- PointExtensions.cs
|   |   |   |   |   |   |-- Models/
|   |   |   |   |   |   |   |-- Element2DOutlineBuilder.cs
|   |   |   |   |   |   |   `-- ParameterToSpeckleData.cs
|   |   |   |   |   |   |-- PartialClasses/
|   |   |   |   |   |   |   |-- ConvertAdaptiveComponent.cs
|   |   |   |   |   |   |   |-- ConvertAnalyticalNode.cs
|   |   |   |   |   |   |   |-- ConvertAnalyticalStick.cs
|   |   |   |   |   |   |   |-- ConvertAnalyticalSurface.cs
|   |   |   |   |   |   |   |-- ConvertArea.cs
|   |   |   |   |   |   |   |-- ConvertBeam.cs
|   |   |   |   |   |   |   |-- ConvertBlock.cs
|   |   |   |   |   |   |   |-- ConvertBrace.cs
|   |   |   |   |   |   |   |-- ConvertBuildingPad.cs
|   |   |   |   |   |   |   |-- ConvertCableTray.cs
|   |   |   |   |   |   |   |-- ConvertCeiling.cs
|   |   |   |   |   |   |   |-- ConvertColumn.cs
|   |   |   |   |   |   |   |-- ConvertCombinableElement.cs
|   |   |   |   |   |   |   |-- ConvertConduit.cs
|   |   |   |   |   |   |   |-- ConvertConnector.cs
|   |   |   |   |   |   |   |-- ConvertCurves.cs
|   |   |   |   |   |   |   |-- ConvertDirectShape.cs
|   |   |   |   |   |   |   |-- ConvertDirectTeklaMeshElements.cs
|   |   |   |   |   |   |   |-- ConvertDisplayableObject.cs
|   |   |   |   |   |   |   |-- ConvertDuct.cs
|   |   |   |   |   |   |   |-- ConvertFabricationPart.cs
|   |   |   |   |   |   |   |-- ConvertFaceWall.cs
|   |   |   |   |   |   |   |-- ConvertFamilyInstance.cs
|   |   |   |   |   |   |   |-- ConvertFitting.cs
|   |   |   |   |   |   |   |-- ConvertFloor.cs
|   |   |   |   |   |   |   |-- ConvertFreeformElement.cs
|   |   |   |   |   |   |   |-- ConvertGeometry.cs
|   |   |   |   |   |   |   |-- ConvertGridLine.cs
|   |   |   |   |   |   |   |-- ConvertGroup.cs
|   |   |   |   |   |   |   |-- ConvertLevel.cs
|   |   |   |   |   |   |   |-- ConvertLocation.cs
|   |   |   |   |   |   |   |-- ConvertMaterial.cs
|   |   |   |   |   |   |   |-- ConvertMaterialQuantities.cs
|   |   |   |   |   |   |   |-- ConvertMEPFamilyInstance.cs
|   |   |   |   |   |   |   |-- ConvertMeshUtils.cs
|   |   |   |   |   |   |   |-- ConvertModel.cs
|   |   |   |   |   |   |   |-- ConvertNetwork.cs
|   |   |   |   |   |   |   |-- ConvertOpening.cs
|   |   |   |   |   |   |   |-- ConvertPanel.cs
|   |   |   |   |   |   |   |-- ConvertPipe.cs
|   |   |   |   |   |   |   |-- ConvertPolygonElement.cs
|   |   |   |   |   |   |   |-- ConvertProfileWall.cs
|   |   |   |   |   |   |   |-- ConvertProjectInfo.cs
|   |   |   |   |   |   |   |-- ConvertRailing.cs
|   |   |   |   |   |   |   |-- ConvertRebar.cs
|   |   |   |   |   |   |   |-- ConvertRevitElement.cs
|   |   |   |   |   |   |   |-- ConvertRoof.cs
|   |   |   |   |   |   |   |-- ConvertRoom.cs
|   |   |   |   |   |   |   |-- ConvertSpace.cs
|   |   |   |   |   |   |   |-- ConvertStair.cs
|   |   |   |   |   |   |   |-- ConvertStructuralConnectionHandlers.cs
|   |   |   |   |   |   |   |-- ConvertStructuralMaterial.cs
|   |   |   |   |   |   |   |-- ConvertStructuralModel.cs
|   |   |   |   |   |   |   |-- ConvertTeklaObjects.cs
|   |   |   |   |   |   |   |-- ConvertTopography.cs
|   |   |   |   |   |   |   |-- ConvertToposolid.cs
|   |   |   |   |   |   |   |-- ConvertTopRail.cs
|   |   |   |   |   |   |   |-- ConvertView.cs
|   |   |   |   |   |   |   |-- ConvertView.Schedule.cs
|   |   |   |   |   |   |   |-- ConvertWall.cs
|   |   |   |   |   |   |   |-- ConvertWire.cs
|   |   |   |   |   |   |   |-- ConvertZone.cs
|   |   |   |   |   |   |   |-- DirectShape.cs
|   |   |   |   |   |   |   |-- Units.cs
|   |   |   |   |   |   |   `-- UpdateParameter.cs
|   |   |   |   |   |   |-- Revit/
|   |   |   |   |   |   |   |-- ConnectionPair.cs
|   |   |   |   |   |   |   `-- FamilyLoadOptions.cs
|   |   |   |   |   |   |-- AllRevitCategories.cs
|   |   |   |   |   |   |-- Categories.cs
|   |   |   |   |   |   |-- ConversionUtils.cs
|   |   |   |   |   |   |-- ConverterRevit.cs
|   |   |   |   |   |   |-- ConverterRevit.DxfImport.cs
|   |   |   |   |   |   |-- ConverterRevit.MeshBuildHelper.cs
|   |   |   |   |   |   |-- ConverterRevit.Previews.cs
|   |   |   |   |   |   |-- ConverterRevit.SettingsHelpers.cs
|   |   |   |   |   |   |-- ConverterRevitShared.projitems
|   |   |   |   |   |   |-- ConverterRevitShared.shproj
|   |   |   |   |   |   |-- DirectContext3DServer.cs
|   |   |   |   |   |   |-- RevitCommitObjectBuilder.cs
|   |   |   |   |   |   |-- RevitCommitObjectBuilderExposer.cs
|   |   |   |   |   |   |-- RevitElementTypeUtils.cs
|   |   |   |   |   |   `-- RevitVersionHelper.cs
|   |   |   |   |   |-- ConverterRevitTests/
|   |   |   |   |   |   |-- ConverterRevitTests2021/
|   |   |   |   |   |   |   `-- ConverterRevitTests2021.csproj
|   |   |   |   |   |   |-- ConverterRevitTests2022/
|   |   |   |   |   |   |   `-- ConverterRevitTests2022.csproj
|   |   |   |   |   |   |-- ConverterRevitTests2023/
|   |   |   |   |   |   |   `-- ConverterRevitTests2023.csproj
|   |   |   |   |   |   |-- ConverterRevitTestsShared/
|   |   |   |   |   |   |   |-- Generated/
|   |   |   |   |   |   |   |   |-- REVIT2021/
|   |   |   |   |   |   |   |   |   `-- TestGenerator/
|   |   |   |   |   |   |   |   |       `-- TestGenerator.Generator/
|   |   |   |   |   |   |   |   |           `-- GeneratedTests.g.cs
|   |   |   |   |   |   |   |   |-- REVIT2022/
|   |   |   |   |   |   |   |   |   `-- TestGenerator/
|   |   |   |   |   |   |   |   |       `-- TestGenerator.Generator/
|   |   |   |   |   |   |   |   |           `-- GeneratedTests.g.cs
|   |   |   |   |   |   |   |   `-- REVIT2023/
|   |   |   |   |   |   |   |       `-- TestGenerator/
|   |   |   |   |   |   |   |           `-- TestGenerator.Generator/
|   |   |   |   |   |   |   |               `-- GeneratedTests.g.cs
|   |   |   |   |   |   |   |-- AssertUtils.cs
|   |   |   |   |   |   |   |-- BrepTests.cs
|   |   |   |   |   |   |   |-- ConverterRevitTestsShared.projitems
|   |   |   |   |   |   |   |-- ConverterRevitTestsShared.shproj
|   |   |   |   |   |   |   |-- Globals.cs
|   |   |   |   |   |   |   |-- SpeckleConversionFixture.cs
|   |   |   |   |   |   |   |-- SpeckleConversionTest.cs
|   |   |   |   |   |   |   |-- SpeckleUtils.cs
|   |   |   |   |   |   |   |-- TestCategories.cs
|   |   |   |   |   |   |   `-- xUnitRevitUtils.cs
|   |   |   |   |   |   `-- TestGenerator/
|   |   |   |   |   |       |-- Categories.cs
|   |   |   |   |   |       |-- Generator.cs
|   |   |   |   |   |       |-- Globals.cs
|   |   |   |   |   |       |-- TestGenerator.csproj
|   |   |   |   |   |       `-- TestTemplate.cs
|   |   |   |   |   |-- Templates/
|   |   |   |   |   |   |-- 2019/
|   |   |   |   |   |   |   |-- Generic Model - Imperial.rft
|   |   |   |   |   |   |   |-- Generic Model - Metric.rft
|   |   |   |   |   |   |   |-- Mass - Imperial.rft
|   |   |   |   |   |   |   `-- Mass - Metric.rft
|   |   |   |   |   |   |-- 2020/
|   |   |   |   |   |   |   |-- Block - Imperial.rft
|   |   |   |   |   |   |   |-- Block - Metric.rft
|   |   |   |   |   |   |   |-- Generic Model - Imperial.rft
|   |   |   |   |   |   |   |-- Generic Model - Metric.rft
|   |   |   |   |   |   |   |-- Mass - Imperial.rft
|   |   |   |   |   |   |   `-- Mass - Metric.rft
|   |   |   |   |   |   |-- 2021/
|   |   |   |   |   |   |   |-- Block - Imperial.rft
|   |   |   |   |   |   |   |-- Block - Metric.rft
|   |   |   |   |   |   |   |-- Generic Model - Imperial.rft
|   |   |   |   |   |   |   |-- Generic Model - Metric.rft
|   |   |   |   |   |   |   |-- Mass - Imperial.rft
|   |   |   |   |   |   |   `-- Mass - Metric.rft
|   |   |   |   |   |   |-- 2022/
|   |   |   |   |   |   |   |-- Block - Imperial.rft
|   |   |   |   |   |   |   |-- Block - Metric.rft
|   |   |   |   |   |   |   |-- Generic Model - Imperial.rft
|   |   |   |   |   |   |   |-- Generic Model - Metric.rft
|   |   |   |   |   |   |   |-- Mass - Imperial.rft
|   |   |   |   |   |   |   `-- Mass - Metric.rft
|   |   |   |   |   |   |-- 2023/
|   |   |   |   |   |   |   |-- Block - Imperial.rft
|   |   |   |   |   |   |   |-- Block - Metric.rft
|   |   |   |   |   |   |   |-- Generic Model - Imperial.rft
|   |   |   |   |   |   |   |-- Generic Model - Metric.rft
|   |   |   |   |   |   |   |-- Mass - Imperial.rft
|   |   |   |   |   |   |   `-- Mass - Metric.rft
|   |   |   |   |   |   |-- 2024/
|   |   |   |   |   |   |   |-- Block - Imperial.rft
|   |   |   |   |   |   |   |-- Block - Metric.rft
|   |   |   |   |   |   |   |-- Generic Model - Imperial.rft
|   |   |   |   |   |   |   |-- Generic Model - Metric.rft
|   |   |   |   |   |   |   |-- Mass - Imperial.rft
|   |   |   |   |   |   |   `-- Mass - Metric.rft
|   |   |   |   |   |   |-- 2025/
|   |   |   |   |   |   |   |-- Block - Imperial.rft
|   |   |   |   |   |   |   |-- Block - Metric.rft
|   |   |   |   |   |   |   |-- Generic Model - Imperial.rft
|   |   |   |   |   |   |   |-- Generic Model - Metric.rft
|   |   |   |   |   |   |   |-- Mass - Imperial.rft
|   |   |   |   |   |   |   `-- Mass - Metric.rft
|   |   |   |   |   |   `-- 2026/
|   |   |   |   |   |       |-- Block - Imperial.rft
|   |   |   |   |   |       |-- Block - Metric.rft
|   |   |   |   |   |       |-- Generic Model - Imperial.rft
|   |   |   |   |   |       |-- Generic Model - Metric.rft
|   |   |   |   |   |       |-- Mass - Imperial.rft
|   |   |   |   |   |       `-- Mass - Metric.rft
|   |   |   |   |   |-- .gitignore
|   |   |   |   |   |-- LICENSE
|   |   |   |   |   `-- README.md
|   |   |   |   |-- ConverterRhinoGh/
|   |   |   |   |   |-- ConverterGrasshopper6/
|   |   |   |   |   |   `-- ConverterGrasshopper6.csproj
|   |   |   |   |   |-- ConverterGrasshopper7/
|   |   |   |   |   |   `-- ConverterGrasshopper7.csproj
|   |   |   |   |   |-- ConverterGrasshopper8/
|   |   |   |   |   |   `-- ConverterGrasshopper8.csproj
|   |   |   |   |   |-- ConverterRhino6/
|   |   |   |   |   |   `-- ConverterRhino6.csproj
|   |   |   |   |   |-- ConverterRhino7/
|   |   |   |   |   |   `-- ConverterRhino7.csproj
|   |   |   |   |   |-- ConverterRhino8/
|   |   |   |   |   |   `-- ConverterRhino8.csproj
|   |   |   |   |   |-- ConverterRhinoGhShared/
|   |   |   |   |   |   |-- BrepEncoder.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.BuiltElements.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.Geometry.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.GIS.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.Mappings.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.Organization.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.Other.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.Structural.cs
|   |   |   |   |   |   |-- ConverterRhinoGh.Utils.cs
|   |   |   |   |   |   |-- ConverterRhinoGhShared.projitems
|   |   |   |   |   |   |-- ConverterRhinoGhShared.shproj
|   |   |   |   |   |   `-- KnotListEncoder.cs
|   |   |   |   |   |-- ConverterRhinoGh.Structural.cs
|   |   |   |   |   `-- LICENSE
|   |   |   |   |-- ConverterRhinoGhTests/
|   |   |   |   |   |-- Geometry/
|   |   |   |   |   |   |-- BrepTests.cs
|   |   |   |   |   |   `-- MeshTest.cs
|   |   |   |   |   |-- ConverterRhinoGhTests.csproj
|   |   |   |   |   `-- RhinoTestFixture.cs
|   |   |   |   |-- ConverterTeklaStructures/
|   |   |   |   |   |-- ConverterTeklaStructures2020/
|   |   |   |   |   |   `-- ConverterTeklaStructures2020.csproj
|   |   |   |   |   |-- ConverterTeklaStructures2021/
|   |   |   |   |   |   `-- ConverterTeklaStructures2021.csproj
|   |   |   |   |   |-- ConverterTeklaStructures2022/
|   |   |   |   |   |   `-- ConverterTeklaStructures2022.csproj
|   |   |   |   |   |-- ConverterTeklaStructures2023/
|   |   |   |   |   |   `-- ConverterTeklaStructures2023.csproj
|   |   |   |   |   `-- ConverterTeklaStructuresShared/
|   |   |   |   |       |-- PartialClasses/
|   |   |   |   |       |   |-- ConvertBeam.cs
|   |   |   |   |       |   |-- ConvertBentPlate.cs
|   |   |   |   |       |   |-- ConvertBolts.cs
|   |   |   |   |       |   |-- ConvertBooleanPart.cs
|   |   |   |   |       |   |-- ConvertContourPlate.cs
|   |   |   |   |       |   |-- ConvertDirectShapeMesh.cs
|   |   |   |   |       |   |-- ConvertFitting.cs
|   |   |   |   |       |   |-- ConvertLoftedPlates.cs
|   |   |   |   |       |   |-- ConvertModel.cs
|   |   |   |   |       |   |-- ConvertPoint.cs
|   |   |   |   |       |   |-- ConvertPolyBeam.cs
|   |   |   |   |       |   |-- ConvertPolygonWelds.cs
|   |   |   |   |       |   |-- ConvertRebar.cs
|   |   |   |   |       |   |-- ConvertSpiralBeam.cs
|   |   |   |   |       |   `-- ConvertWelds.cs
|   |   |   |   |       |-- ConverterTeklaStructures.cs
|   |   |   |   |       |-- ConverterTeklaStructuresShared.projitems
|   |   |   |   |       |-- ConverterTeklaStructuresShared.shproj
|   |   |   |   |       `-- ConverterTeklaStructureUtils.cs
|   |   |   |   `-- StructuralUtilities/
|   |   |   |       `-- PolygonMesher/
|   |   |   |           |-- ClosedLoop.cs
|   |   |   |           |-- Extensions.cs
|   |   |   |           |-- IndexPair.cs
|   |   |   |           |-- IndexSet.cs
|   |   |   |           |-- PolygonMesher.cs
|   |   |   |           |-- PolygonMesher.csproj
|   |   |   |           |-- TriangleIndexSet.cs
|   |   |   |           `-- Vertex.cs
|   |   |   |-- Objects/
|   |   |   |   |-- BuiltElements/
|   |   |   |   |   |-- AdvanceSteel/
|   |   |   |   |   |   |-- AsteelBeam.cs
|   |   |   |   |   |   |-- AsteelBolt.cs
|   |   |   |   |   |   |-- AsteelGrating.cs
|   |   |   |   |   |   |-- AsteelPlate.cs
|   |   |   |   |   |   |-- AsteelPolyBeam.cs
|   |   |   |   |   |   |-- AsteelSectionProfile.cs
|   |   |   |   |   |   |-- AsteelSectionProfileDB.cs
|   |   |   |   |   |   |-- AsteelSlab.cs
|   |   |   |   |   |   |-- AsteelSpecialPart.cs
|   |   |   |   |   |   |-- AsteelStraightBeam.cs
|   |   |   |   |   |   |-- Enums.cs
|   |   |   |   |   |   `-- IAsteelObject.cs
|   |   |   |   |   |-- Archicad/
|   |   |   |   |   |   |-- ArchicadBeam.cs
|   |   |   |   |   |   |-- ArchicadColumn.cs
|   |   |   |   |   |   |-- ArchicadFloor.cs
|   |   |   |   |   |   |-- ArchicadLevel.cs
|   |   |   |   |   |   |-- ArchicadOpening.cs
|   |   |   |   |   |   |-- ArchicadRoof.cs
|   |   |   |   |   |   |-- ArchicadRoom.cs
|   |   |   |   |   |   |-- ArchicadWall.cs
|   |   |   |   |   |   |-- AssemblySegment.cs
|   |   |   |   |   |   |-- Classification.cs
|   |   |   |   |   |   |-- ComponentProperties.cs
|   |   |   |   |   |   |-- DirectShape.cs
|   |   |   |   |   |   |-- ElementShape.cs
|   |   |   |   |   |   |-- Fenestration.cs
|   |   |   |   |   |   |-- Property.cs
|   |   |   |   |   |   `-- PropertyGroup.cs
|   |   |   |   |   |-- Civil/
|   |   |   |   |   |   |-- CivilAlignment.cs
|   |   |   |   |   |   |-- CivilAppliedAssembly.cs
|   |   |   |   |   |   |-- CivilAppliedSubassembly.cs
|   |   |   |   |   |   |-- CivilBaseline.cs
|   |   |   |   |   |   |-- CivilBaselineRegion.cs
|   |   |   |   |   |   |-- CivilCalculatedLink.cs
|   |   |   |   |   |   |-- CivilCalculatedPoint.cs
|   |   |   |   |   |   |-- CivilCalculatedShape.cs
|   |   |   |   |   |   `-- CivilProfile.cs
|   |   |   |   |   |-- Revit/
|   |   |   |   |   |   |-- Curve/
|   |   |   |   |   |   |   `-- ModelCurves.cs
|   |   |   |   |   |   |-- Interfaces/
|   |   |   |   |   |   |   `-- IHasMEPConnectors.cs
|   |   |   |   |   |   |-- RevitRoof/
|   |   |   |   |   |   |   `-- RevitRoof.cs
|   |   |   |   |   |   |-- AdaptiveComponent.cs
|   |   |   |   |   |   |-- BuildingPad.cs
|   |   |   |   |   |   |-- DirectShape.cs
|   |   |   |   |   |   |-- Enums.cs
|   |   |   |   |   |   |-- FamilyInstance.cs
|   |   |   |   |   |   |-- FreeformElement.cs
|   |   |   |   |   |   |-- MEPFamilyInstance.cs
|   |   |   |   |   |   |-- Parameter.cs
|   |   |   |   |   |   |-- ParameterUpdater.cs
|   |   |   |   |   |   |-- ProjectInfo.cs
|   |   |   |   |   |   |-- RevitBeam.cs
|   |   |   |   |   |   |-- RevitBrace.cs
|   |   |   |   |   |   |-- RevitCableTray.cs
|   |   |   |   |   |   |-- RevitCeiling.cs
|   |   |   |   |   |   |-- RevitColumn.cs
|   |   |   |   |   |   |-- RevitConduit.cs
|   |   |   |   |   |   |-- RevitCurtainWallPanel.cs
|   |   |   |   |   |   |-- RevitDuct.cs
|   |   |   |   |   |   |-- RevitElement.cs
|   |   |   |   |   |   |-- RevitElementType.cs
|   |   |   |   |   |   |-- RevitFloor.cs
|   |   |   |   |   |   |-- RevitLevel.cs
|   |   |   |   |   |   |-- RevitMEPConnector.cs
|   |   |   |   |   |   |-- RevitNetwork.cs
|   |   |   |   |   |   |-- RevitOpening.cs
|   |   |   |   |   |   |-- RevitPipe.cs
|   |   |   |   |   |   |-- RevitRailing.cs
|   |   |   |   |   |   |-- RevitRebar.cs
|   |   |   |   |   |   |-- RevitStair.cs
|   |   |   |   |   |   |-- RevitTopography.cs
|   |   |   |   |   |   |-- RevitToposolid.cs
|   |   |   |   |   |   |-- RevitWall.cs
|   |   |   |   |   |   |-- RevitWire.cs
|   |   |   |   |   |   |-- RevitZone.cs
|   |   |   |   |   |   `-- StructuralConnectionHandler.cs
|   |   |   |   |   |-- TeklaStructures/
|   |   |   |   |   |   |-- BeamPosition.cs
|   |   |   |   |   |   |-- Bolts.cs
|   |   |   |   |   |   |-- Enums.cs
|   |   |   |   |   |   |-- Fitting.cs
|   |   |   |   |   |   |-- TeklaBeam.cs
|   |   |   |   |   |   |-- TeklaContourPlate.cs
|   |   |   |   |   |   |-- TeklaModel.cs
|   |   |   |   |   |   |-- TeklaOpening.cs
|   |   |   |   |   |   |-- TeklaRebar.cs
|   |   |   |   |   |   `-- Welds.cs
|   |   |   |   |   |-- Alignment.cs
|   |   |   |   |   |-- Area.cs
|   |   |   |   |   |-- Baseline.cs
|   |   |   |   |   |-- Beam.cs
|   |   |   |   |   |-- Brace.cs
|   |   |   |   |   |-- CableTray.cs
|   |   |   |   |   |-- Ceiling.cs
|   |   |   |   |   |-- Column.cs
|   |   |   |   |   |-- Conduit.cs
|   |   |   |   |   |-- Duct.cs
|   |   |   |   |   |-- Featureline.cs
|   |   |   |   |   |-- Floor.cs
|   |   |   |   |   |-- GridLine.cs
|   |   |   |   |   |-- Level.cs
|   |   |   |   |   |-- Network.cs
|   |   |   |   |   |-- Opening.cs
|   |   |   |   |   |-- Pipe.cs
|   |   |   |   |   |-- Profile.cs
|   |   |   |   |   |-- Rebar.cs
|   |   |   |   |   |-- Roof.cs
|   |   |   |   |   |-- Room.cs
|   |   |   |   |   |-- Space.cs
|   |   |   |   |   |-- Station.cs
|   |   |   |   |   |-- Structure.cs
|   |   |   |   |   |-- Topography.cs
|   |   |   |   |   |-- View.cs
|   |   |   |   |   |-- Wall.cs
|   |   |   |   |   |-- Wire.cs
|   |   |   |   |   `-- Zone.cs
|   |   |   |   |-- Geometry/
|   |   |   |   |   |-- Arc.cs
|   |   |   |   |   |-- Box.cs
|   |   |   |   |   |-- Brep.cs
|   |   |   |   |   |-- BrepEdge.cs
|   |   |   |   |   |-- BrepFace.cs
|   |   |   |   |   |-- BrepLoop.cs
|   |   |   |   |   |-- BrepTrim.cs
|   |   |   |   |   |-- Circle.cs
|   |   |   |   |   |-- ControlPoint.cs
|   |   |   |   |   |-- Curve.cs
|   |   |   |   |   |-- Ellipse.cs
|   |   |   |   |   |-- Extrusion.cs
|   |   |   |   |   |-- Line.cs
|   |   |   |   |   |-- Mesh.cs
|   |   |   |   |   |-- Plane.cs
|   |   |   |   |   |-- Point.cs
|   |   |   |   |   |-- Pointcloud.cs
|   |   |   |   |   |-- Polycurve.cs
|   |   |   |   |   |-- Polyline.cs
|   |   |   |   |   |-- PolylineExtensions.cs
|   |   |   |   |   |-- Spiral.cs
|   |   |   |   |   |-- Surface.cs
|   |   |   |   |   `-- Vector.cs
|   |   |   |   |-- GIS/
|   |   |   |   |   |-- GisFeature.cs
|   |   |   |   |   |-- GisTopography.cs
|   |   |   |   |   `-- PolygonElement.cs
|   |   |   |   |-- Organization/
|   |   |   |   |   |-- Deprecated/
|   |   |   |   |   |   `-- Collection.cs
|   |   |   |   |   |-- DataTable.cs
|   |   |   |   |   `-- Model.cs
|   |   |   |   |-- Other/
|   |   |   |   |   |-- Civil/
|   |   |   |   |   |   `-- CivilDataField.cs
|   |   |   |   |   |-- Revit/
|   |   |   |   |   |   |-- RevitInstance.cs
|   |   |   |   |   |   `-- RevitMaterial.cs
|   |   |   |   |   |-- Block.cs
|   |   |   |   |   |-- DataField.cs
|   |   |   |   |   |-- Dimension.cs
|   |   |   |   |   |-- DisplayStyle.cs
|   |   |   |   |   |-- Hatch.cs
|   |   |   |   |   |-- Instance.cs
|   |   |   |   |   |-- MappedBlockWrapper.cs
|   |   |   |   |   |-- Material.cs
|   |   |   |   |   |-- MaterialQuantity.cs
|   |   |   |   |   |-- RenderMaterial.cs
|   |   |   |   |   |-- Text.cs
|   |   |   |   |   `-- Transform.cs
|   |   |   |   |-- Primitive/
|   |   |   |   |   |-- Chunk.cs
|   |   |   |   |   |-- Interval.cs
|   |   |   |   |   `-- Interval2d.cs
|   |   |   |   |-- Structural/
|   |   |   |   |   |-- Analysis/
|   |   |   |   |   |   |-- Model.cs
|   |   |   |   |   |   |-- ModelInfo.cs
|   |   |   |   |   |   |-- ModelSettings.cs
|   |   |   |   |   |   |-- ModelUnits.cs
|   |   |   |   |   |   `-- UnitTypes.cs
|   |   |   |   |   |-- CSI/
|   |   |   |   |   |   |-- Analysis/
|   |   |   |   |   |   |   |-- CSIStories.cs
|   |   |   |   |   |   |   |-- ETABSAnalysis.cs
|   |   |   |   |   |   |   |-- ETABSAreaType.cs
|   |   |   |   |   |   |   `-- ETABSLoadingType.cs
|   |   |   |   |   |   |-- Geometry/
|   |   |   |   |   |   |   |-- CSIElement1D.cs
|   |   |   |   |   |   |   |-- CSIElement2D.cs
|   |   |   |   |   |   |   |-- CSIGridLines.cs
|   |   |   |   |   |   |   |-- CSINode.cs
|   |   |   |   |   |   |   |-- CSIPier.cs
|   |   |   |   |   |   |   |-- CSISpandrel.cs
|   |   |   |   |   |   |   `-- CSITendon.cs
|   |   |   |   |   |   |-- Loading/
|   |   |   |   |   |   |   `-- CSIWindLoading.cs
|   |   |   |   |   |   |-- Materials/
|   |   |   |   |   |   |   |-- CSIConcrete.cs
|   |   |   |   |   |   |   |-- CSIRebar.cs
|   |   |   |   |   |   |   `-- CSISteel.cs
|   |   |   |   |   |   `-- Properties/
|   |   |   |   |   |       |-- CSIDiaphragm.cs
|   |   |   |   |   |       |-- CSILinkProperty.cs
|   |   |   |   |   |       |-- CSIProperty2D.cs
|   |   |   |   |   |       |-- CSISpringProperty.cs
|   |   |   |   |   |       |-- CSITendonProperty.cs
|   |   |   |   |   |       `-- ETABSProperty.cs
|   |   |   |   |   |-- Geometry/
|   |   |   |   |   |   |-- Axis.cs
|   |   |   |   |   |   |-- Element1D.cs
|   |   |   |   |   |   |-- Element2D.cs
|   |   |   |   |   |   |-- Element3D.cs
|   |   |   |   |   |   |-- ElementType.cs
|   |   |   |   |   |   |-- MemberType.cs
|   |   |   |   |   |   |-- MemberType1D.cs
|   |   |   |   |   |   |-- Node.cs
|   |   |   |   |   |   |-- Restraint.cs
|   |   |   |   |   |   |-- RestraintType.cs
|   |   |   |   |   |   `-- Storey.cs
|   |   |   |   |   |-- GSA/
|   |   |   |   |   |   |-- Analysis/
|   |   |   |   |   |   |   |-- GSAAnalysisCase.cs
|   |   |   |   |   |   |   |-- GSAStage.cs
|   |   |   |   |   |   |   `-- GSATask.cs
|   |   |   |   |   |   |-- Bridge/
|   |   |   |   |   |   |   |-- GSAAlignment.cs
|   |   |   |   |   |   |   |-- GSAInfluence.cs
|   |   |   |   |   |   |   |-- GSAInfluenceBeam.cs
|   |   |   |   |   |   |   |-- GSAInfluenceNode.cs
|   |   |   |   |   |   |   |-- GSAPath.cs
|   |   |   |   |   |   |   `-- GSAUserVehicle.cs
|   |   |   |   |   |   |-- Geometry/
|   |   |   |   |   |   |   |-- GSAAssembly.cs
|   |   |   |   |   |   |   |-- GSAElement1D.cs
|   |   |   |   |   |   |   |-- GSAElement2D.cs
|   |   |   |   |   |   |   |-- GSAElement3D.cs
|   |   |   |   |   |   |   |-- GSAGeneralisedRestraint.cs
|   |   |   |   |   |   |   |-- GSAGridLine.cs
|   |   |   |   |   |   |   |-- GSAGridPlane.cs
|   |   |   |   |   |   |   |-- GSAGridSurface.cs
|   |   |   |   |   |   |   |-- GSAMember1D.cs
|   |   |   |   |   |   |   |-- GSAMember2D.cs
|   |   |   |   |   |   |   |-- GSANode.cs
|   |   |   |   |   |   |   |-- GSARigidConstraint.cs
|   |   |   |   |   |   |   `-- GSAStorey.cs
|   |   |   |   |   |   |-- Loading/
|   |   |   |   |   |   |   |-- GSALoadBeam.cs
|   |   |   |   |   |   |   |-- GSALoadCase.cs
|   |   |   |   |   |   |   |-- GSALoadCombination.cs
|   |   |   |   |   |   |   |-- GSALoadFace.cs
|   |   |   |   |   |   |   |-- GSALoadGravity.cs
|   |   |   |   |   |   |   |-- GSALoadGrid.cs
|   |   |   |   |   |   |   |-- GSALoadGridArea.cs
|   |   |   |   |   |   |   |-- GSALoadGridLine.cs
|   |   |   |   |   |   |   |-- GSALoadGridPoint.cs
|   |   |   |   |   |   |   |-- GSALoadNode.cs
|   |   |   |   |   |   |   |-- GSALoadThermal2d.cs
|   |   |   |   |   |   |   `-- GSAPolyline.cs
|   |   |   |   |   |   |-- Materials/
|   |   |   |   |   |   |   |-- GSAConcrete.cs
|   |   |   |   |   |   |   |-- GSAMaterial.cs
|   |   |   |   |   |   |   `-- GSASteel.cs
|   |   |   |   |   |   `-- Properties/
|   |   |   |   |   |       |-- GSAProperty1D.cs
|   |   |   |   |   |       `-- GSAProperty2D.cs
|   |   |   |   |   |-- Loading/
|   |   |   |   |   |   |-- Load.cs
|   |   |   |   |   |   |-- LoadBeam.cs
|   |   |   |   |   |   |-- LoadCase.cs
|   |   |   |   |   |   |-- LoadCombination.cs
|   |   |   |   |   |   |-- LoadFace.cs
|   |   |   |   |   |   |-- LoadGravity.cs
|   |   |   |   |   |   |-- LoadNode.cs
|   |   |   |   |   |   `-- Loads.cs
|   |   |   |   |   |-- Materials/
|   |   |   |   |   |   |-- Concrete.cs
|   |   |   |   |   |   |-- Steel.cs
|   |   |   |   |   |   |-- StructuralMaterial.cs
|   |   |   |   |   |   `-- Timber.cs
|   |   |   |   |   |-- Properties/
|   |   |   |   |   |   |-- Profiles/
|   |   |   |   |   |   |   `-- SectionProfile.cs
|   |   |   |   |   |   |-- Property.cs
|   |   |   |   |   |   |-- Property1D.cs
|   |   |   |   |   |   |-- Property2D.cs
|   |   |   |   |   |   |-- Property3D.cs
|   |   |   |   |   |   |-- PropertyDamper.cs
|   |   |   |   |   |   |-- PropertyMass.cs
|   |   |   |   |   |   `-- PropertySpring.cs
|   |   |   |   |   |-- Results/
|   |   |   |   |   |   |-- AnalyticalResults.cs
|   |   |   |   |   |   |-- Result.cs
|   |   |   |   |   |   |-- Result1D.cs
|   |   |   |   |   |   |-- Result2D.cs
|   |   |   |   |   |   |-- Result3D.cs
|   |   |   |   |   |   |-- ResultAll.cs
|   |   |   |   |   |   |-- ResultGlobal.cs
|   |   |   |   |   |   `-- ResultNode.cs
|   |   |   |   |   |-- Axis.cs
|   |   |   |   |   |-- MaterialType.cs
|   |   |   |   |   `-- PropertyType.cs
|   |   |   |   |-- Utils/
|   |   |   |   |   |-- MeshTriangulationHelper.cs
|   |   |   |   |   `-- Parameters.cs
|   |   |   |   |-- .editorconfig
|   |   |   |   |-- EncodingOptimisations.cs
|   |   |   |   |-- Interfaces.cs
|   |   |   |   |-- Objects.csproj
|   |   |   |   `-- ObjectsKit.cs
|   |   |   |-- Tests/
|   |   |   |   `-- Objects.Tests.Unit/
|   |   |   |       |-- Geometry/
|   |   |   |       |   |-- ArcTests.cs
|   |   |   |       |   |-- MeshTests.cs
|   |   |   |       |   |-- PointTests.cs
|   |   |   |       |   `-- TransformTests.cs
|   |   |   |       |-- Utils/
|   |   |   |       |   |-- MeshTriangulationHelperTests.cs
|   |   |   |       |   `-- ShallowCopyTests.cs
|   |   |   |       |-- GenericTests.cs
|   |   |   |       |-- ModelPropertySupportedTypes.cs
|   |   |   |       |-- NUnit_Fixtures.cs
|   |   |   |       `-- Objects.Tests.Unit.csproj
|   |   |   |-- Directory.Build.props
|   |   |   |-- Objects.sln
|   |   |   `-- README.md
|   |   |-- .csharpierrc.yaml
|   |   |-- .editorconfig
|   |   |-- .gitguardian.yml
|   |   |-- .gitignore
|   |   |-- .gitmodules
|   |   |-- All.sln
|   |   |-- All.sln.DotSettings
|   |   |-- CodeMetricsConfig.txt
|   |   |-- Directory.Build.props
|   |   |-- Directory.Build.targets
|   |   |-- global.json
|   |   |-- LICENSE
|   |   |-- README.md
|   |   |-- SDK.slnf
|   |   `-- SECURITY.md
|   |-- dataprocessing/
|   |   |-- florence_embedding/
|   |   |   |-- building_synthesis/
|   |   |   |   |-- building_info_25-01-001.json
|   |   |   |   |-- building_info_25-01-002.json
|   |   |   |   |-- building_info_25-01-004.json
|   |   |   |   |-- building_info_25-01-005.json
|   |   |   |   |-- building_info_25-01-006.json
|   |   |   |   |-- building_info_25-01-008.json
|   |   |   |   |-- building_info_25-01-010.json
|   |   |   |   |-- building_info_25-01-011.json
|   |   |   |   |-- building_info_25-01-012.json
|   |   |   |   |-- building_info_25-01-013.json
|   |   |   |   |-- building_info_25-01-014.json
|   |   |   |   |-- building_info_25-01-017.json
|   |   |   |   |-- building_info_25-01-018.json
|   |   |   |   |-- building_info_25-01-019.json
|   |   |   |   |-- building_info_25-01-020.json
|   |   |   |   |-- building_info_25-01-021.json
|   |   |   |   |-- building_info_25-01-023.json
|   |   |   |   |-- building_info_25-01-024.json
|   |   |   |   |-- building_info_25-01-025.json
|   |   |   |   |-- building_info_25-01-026.json
|   |   |   |   |-- building_info_25-01-027.json
|   |   |   |   |-- building_info_25-01-028.json
|   |   |   |   |-- building_info_25-01-035.json
|   |   |   |   |-- building_info_25-01-036.json
|   |   |   |   |-- building_info_25-01-037.json
|   |   |   |   |-- building_info_25-01-038.json
|   |   |   |   |-- building_info_25-01-039.json
|   |   |   |   |-- building_info_25-01-040.json
|   |   |   |   |-- building_info_25-01-041.json
|   |   |   |   |-- building_info_25-01-042.json
|   |   |   |   |-- building_info_25-01-043.json
|   |   |   |   |-- building_info_25-01-044.json
|   |   |   |   |-- building_info_25-01-045.json
|   |   |   |   |-- building_info_25-01-060.json
|   |   |   |   |-- building_info_25-01-064.json
|   |   |   |   |-- building_info_25-01-067.json
|   |   |   |   |-- building_info_25-01-068.json
|   |   |   |   |-- building_info_25-01-069.json
|   |   |   |   |-- building_info_25-01-070.json
|   |   |   |   |-- building_info_25-01-073.json
|   |   |   |   |-- building_info_25-01-074.json
|   |   |   |   |-- building_info_25-01-075.json
|   |   |   |   |-- building_info_25-01-078.json
|   |   |   |   |-- building_info_25-01-079.json
|   |   |   |   |-- building_info_25-01-080.json
|   |   |   |   |-- building_info_25-01-081.json
|   |   |   |   |-- building_info_25-01-082.json
|   |   |   |   |-- building_info_25-01-083.json
|   |   |   |   |-- building_info_25-01-084.json
|   |   |   |   |-- building_info_25-01-085.json
|   |   |   |   |-- building_info_25-01-086.json
|   |   |   |   |-- building_info_25-01-087.json
|   |   |   |   |-- building_info_25-01-095.json
|   |   |   |   |-- building_info_25-01-096.json
|   |   |   |   |-- building_info_25-01-097.json
|   |   |   |   |-- building_info_25-01-098.json
|   |   |   |   |-- building_info_25-01-099.json
|   |   |   |   |-- building_info_25-01-100.json
|   |   |   |   |-- building_info_25-01-101.json
|   |   |   |   |-- building_info_25-01-102.json
|   |   |   |   `-- building_info_25-01-105.json
|   |   |   |-- embeddings_florence/
|   |   |   |   |-- config.json
|   |   |   |   `-- metadata.json
|   |   |   |-- florence_json/
|   |   |   |   `-- 25-01-005/
|   |   |   |       |-- Clare Brubacher goat barn (25-01-005)_page_001.json
|   |   |   |       |-- Clare Brubacher goat barn (25-01-005)_page_002.json
|   |   |   |       |-- Clare Brubacher goat barn (25-01-005)_page_003.json
|   |   |   |       |-- Clare Brubacher goat barn (25-01-005)_page_004.json
|   |   |   |       |-- Clare Brubacher goat barn (25-01-005)_page_005.json
|   |   |   |       |-- Clare Brubacher goat barn (25-01-005)_page_006.json
|   |   |   |       |-- region_01_red_box.json
|   |   |   |       |-- region_02_red_box.json
|   |   |   |       |-- region_03_red_box.json
|   |   |   |       |-- region_04_red_box.json
|   |   |   |       |-- region_05_red_box.json
|   |   |   |       `-- region_06_red_box.json
|   |   |   |-- imageCHAT/
|   |   |   |   |-- embedding_utils.py
|   |   |   |   |-- gpt4o_utils.py
|   |   |   |   |-- langgraph_orchestrator.py
|   |   |   |   |-- requirements.txt
|   |   |   |   |-- STREAMLIT_APP_README.md
|   |   |   |   |-- streamlit_chat_app.py
|   |   |   |   `-- supabase_utils.py
|   |   |   |-- structured_json/
|   |   |   |   |-- 25-01-001/
|   |   |   |   |   |-- page_metadata_25-01-001.json
|   |   |   |   |   `-- structured_25-01-001.json
|   |   |   |   |-- 25-01-002/
|   |   |   |   |   |-- page_metadata_25-01-002.json
|   |   |   |   |   `-- structured_25-01-002.json
|   |   |   |   |-- 25-01-003/
|   |   |   |   |   `-- page_metadata_25-01-003.json
|   |   |   |   |-- 25-01-004/
|   |   |   |   |   |-- page_metadata_25-01-004.json
|   |   |   |   |   `-- structured_25-01-004.json
|   |   |   |   |-- 25-01-005/
|   |   |   |   |   |-- page_metadata_25-01-005.json
|   |   |   |   |   `-- structured_25-01-005.json
|   |   |   |   |-- 25-01-006/
|   |   |   |   |   |-- page_metadata_25-01-006.json
|   |   |   |   |   `-- structured_25-01-006.json
|   |   |   |   |-- 25-01-008/
|   |   |   |   |   |-- page_metadata_25-01-008.json
|   |   |   |   |   `-- structured_25-01-008.json
|   |   |   |   |-- 25-01-010/
|   |   |   |   |   |-- debug_response_region_02_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-010.json
|   |   |   |   |   `-- structured_25-01-010.json
|   |   |   |   |-- 25-01-011/
|   |   |   |   |   |-- page_metadata_25-01-011.json
|   |   |   |   |   `-- structured_25-01-011.json
|   |   |   |   |-- 25-01-012/
|   |   |   |   |   |-- page_metadata_25-01-012.json
|   |   |   |   |   `-- structured_25-01-012.json
|   |   |   |   |-- 25-01-013/
|   |   |   |   |   |-- page_metadata_25-01-013.json
|   |   |   |   |   `-- structured_25-01-013.json
|   |   |   |   |-- 25-01-014/
|   |   |   |   |   |-- page_metadata_25-01-014.json
|   |   |   |   |   `-- structured_25-01-014.json
|   |   |   |   |-- 25-01-015/
|   |   |   |   |   `-- page_metadata_25-01-015.json
|   |   |   |   |-- 25-01-017/
|   |   |   |   |   |-- debug_response_region_01_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-017.json
|   |   |   |   |   `-- structured_25-01-017.json
|   |   |   |   |-- 25-01-018/
|   |   |   |   |   |-- page_metadata_25-01-018.json
|   |   |   |   |   `-- structured_25-01-018.json
|   |   |   |   |-- 25-01-019/
|   |   |   |   |   |-- page_metadata_25-01-019.json
|   |   |   |   |   `-- structured_25-01-019.json
|   |   |   |   |-- 25-01-020/
|   |   |   |   |   |-- page_metadata_25-01-020.json
|   |   |   |   |   `-- structured_25-01-020.json
|   |   |   |   |-- 25-01-021/
|   |   |   |   |   |-- page_metadata_25-01-021.json
|   |   |   |   |   `-- structured_25-01-021.json
|   |   |   |   |-- 25-01-023/
|   |   |   |   |   |-- page_metadata_25-01-023.json
|   |   |   |   |   `-- structured_25-01-023.json
|   |   |   |   |-- 25-01-024/
|   |   |   |   |   |-- page_metadata_25-01-024.json
|   |   |   |   |   `-- structured_25-01-024.json
|   |   |   |   |-- 25-01-025/
|   |   |   |   |   |-- page_metadata_25-01-025.json
|   |   |   |   |   `-- structured_25-01-025.json
|   |   |   |   |-- 25-01-026/
|   |   |   |   |   |-- debug_response_region_01_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-026.json
|   |   |   |   |   `-- structured_25-01-026.json
|   |   |   |   |-- 25-01-027/
|   |   |   |   |   |-- page_metadata_25-01-027.json
|   |   |   |   |   `-- structured_25-01-027.json
|   |   |   |   |-- 25-01-028/
|   |   |   |   |   |-- page_metadata_25-01-028.json
|   |   |   |   |   `-- structured_25-01-028.json
|   |   |   |   |-- 25-01-035/
|   |   |   |   |   |-- page_metadata_25-01-035.json
|   |   |   |   |   `-- structured_25-01-035.json
|   |   |   |   |-- 25-01-036/
|   |   |   |   |   |-- page_metadata_25-01-036.json
|   |   |   |   |   `-- structured_25-01-036.json
|   |   |   |   |-- 25-01-037/
|   |   |   |   |   |-- page_metadata_25-01-037.json
|   |   |   |   |   `-- structured_25-01-037.json
|   |   |   |   |-- 25-01-038/
|   |   |   |   |   |-- page_metadata_25-01-038.json
|   |   |   |   |   `-- structured_25-01-038.json
|   |   |   |   |-- 25-01-039/
|   |   |   |   |   |-- debug_response_region_01_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-039.json
|   |   |   |   |   `-- structured_25-01-039.json
|   |   |   |   |-- 25-01-040/
|   |   |   |   |   |-- page_metadata_25-01-040.json
|   |   |   |   |   `-- structured_25-01-040.json
|   |   |   |   |-- 25-01-041/
|   |   |   |   |   |-- page_metadata_25-01-041.json
|   |   |   |   |   `-- structured_25-01-041.json
|   |   |   |   |-- 25-01-042/
|   |   |   |   |   |-- page_metadata_25-01-042.json
|   |   |   |   |   `-- structured_25-01-042.json
|   |   |   |   |-- 25-01-043/
|   |   |   |   |   |-- debug_response_region_01_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-043.json
|   |   |   |   |   `-- structured_25-01-043.json
|   |   |   |   |-- 25-01-044/
|   |   |   |   |   |-- page_metadata_25-01-044.json
|   |   |   |   |   `-- structured_25-01-044.json
|   |   |   |   |-- 25-01-045/
|   |   |   |   |   |-- page_metadata_25-01-045.json
|   |   |   |   |   `-- structured_25-01-045.json
|   |   |   |   |-- 25-01-060/
|   |   |   |   |   |-- debug_response_region_02_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-060.json
|   |   |   |   |   `-- structured_25-01-060.json
|   |   |   |   |-- 25-01-064/
|   |   |   |   |   |-- page_metadata_25-01-064.json
|   |   |   |   |   `-- structured_25-01-064.json
|   |   |   |   |-- 25-01-067/
|   |   |   |   |   |-- page_metadata_25-01-067.json
|   |   |   |   |   `-- structured_25-01-067.json
|   |   |   |   |-- 25-01-068/
|   |   |   |   |   |-- page_metadata_25-01-068.json
|   |   |   |   |   `-- structured_25-01-068.json
|   |   |   |   |-- 25-01-069/
|   |   |   |   |   |-- page_metadata_25-01-069.json
|   |   |   |   |   `-- structured_25-01-069.json
|   |   |   |   |-- 25-01-070/
|   |   |   |   |   |-- page_metadata_25-01-070.json
|   |   |   |   |   `-- structured_25-01-070.json
|   |   |   |   |-- 25-01-073/
|   |   |   |   |   |-- page_metadata_25-01-073.json
|   |   |   |   |   `-- structured_25-01-073.json
|   |   |   |   |-- 25-01-074/
|   |   |   |   |   |-- page_metadata_25-01-074.json
|   |   |   |   |   `-- structured_25-01-074.json
|   |   |   |   |-- 25-01-075/
|   |   |   |   |   |-- debug_response_region_05_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-075.json
|   |   |   |   |   `-- structured_25-01-075.json
|   |   |   |   |-- 25-01-078/
|   |   |   |   |   |-- page_metadata_25-01-078.json
|   |   |   |   |   `-- structured_25-01-078.json
|   |   |   |   |-- 25-01-079/
|   |   |   |   |   |-- page_metadata_25-01-079.json
|   |   |   |   |   `-- structured_25-01-079.json
|   |   |   |   |-- 25-01-080/
|   |   |   |   |   |-- page_metadata_25-01-080.json
|   |   |   |   |   `-- structured_25-01-080.json
|   |   |   |   |-- 25-01-081/
|   |   |   |   |   |-- debug_response_region_01_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-081.json
|   |   |   |   |   `-- structured_25-01-081.json
|   |   |   |   |-- 25-01-082/
|   |   |   |   |   |-- page_metadata_25-01-082.json
|   |   |   |   |   `-- structured_25-01-082.json
|   |   |   |   |-- 25-01-083/
|   |   |   |   |   |-- page_metadata_25-01-083.json
|   |   |   |   |   `-- structured_25-01-083.json
|   |   |   |   |-- 25-01-084/
|   |   |   |   |   |-- page_metadata_25-01-084.json
|   |   |   |   |   `-- structured_25-01-084.json
|   |   |   |   |-- 25-01-085/
|   |   |   |   |   |-- page_metadata_25-01-085.json
|   |   |   |   |   `-- structured_25-01-085.json
|   |   |   |   |-- 25-01-086/
|   |   |   |   |   |-- page_metadata_25-01-086.json
|   |   |   |   |   `-- structured_25-01-086.json
|   |   |   |   |-- 25-01-087/
|   |   |   |   |   |-- page_metadata_25-01-087.json
|   |   |   |   |   `-- structured_25-01-087.json
|   |   |   |   |-- 25-01-095/
|   |   |   |   |   |-- page_metadata_25-01-095.json
|   |   |   |   |   `-- structured_25-01-095.json
|   |   |   |   |-- 25-01-096/
|   |   |   |   |   |-- page_metadata_25-01-096.json
|   |   |   |   |   `-- structured_25-01-096.json
|   |   |   |   |-- 25-01-097/
|   |   |   |   |   |-- debug_response_region_01_red_box.png.txt
|   |   |   |   |   |-- page_metadata_25-01-097.json
|   |   |   |   |   `-- structured_25-01-097.json
|   |   |   |   |-- 25-01-098/
|   |   |   |   |   |-- page_metadata_25-01-098.json
|   |   |   |   |   `-- structured_25-01-098.json
|   |   |   |   |-- 25-01-099/
|   |   |   |   |   |-- page_metadata_25-01-099.json
|   |   |   |   |   `-- structured_25-01-099.json
|   |   |   |   |-- 25-01-100/
|   |   |   |   |   |-- page_metadata_25-01-100.json
|   |   |   |   |   `-- structured_25-01-100.json
|   |   |   |   |-- 25-01-101/
|   |   |   |   |   |-- page_metadata_25-01-101.json
|   |   |   |   |   `-- structured_25-01-101.json
|   |   |   |   |-- 25-01-102/
|   |   |   |   |   |-- page_metadata_25-01-102.json
|   |   |   |   |   `-- structured_25-01-102.json
|   |   |   |   `-- 25-01-105/
|   |   |   |       |-- page_metadata_25-01-105.json
|   |   |   |       `-- structured_25-01-105.json
|   |   |   |-- batch_process_25-01.py
|   |   |   |-- batch_synthesize_building_info.py
|   |   |   |-- batch_upload_building_info.py
|   |   |   |-- batch_upload_to_supabase.py
|   |   |   |-- copy_of_projects_master_json.py
|   |   |   |-- create_image_descriptions_table.sql
|   |   |   |-- create_project_description_table.sql
|   |   |   |-- download_florence2.py
|   |   |   |-- embed_screenshots.py
|   |   |   |-- embedding_utils.py
|   |   |   |-- export_to_supabase.py
|   |   |   |-- extract_structured_info.py
|   |   |   |-- flash_attn_stub.py
|   |   |   |-- gpt4o_utils.py
|   |   |   |-- json_to_supabase.py
|   |   |   |-- JSON_TO_SUPABASE_README.md
|   |   |   |-- README_FLASH_ATTN.md
|   |   |   |-- requirements.txt
|   |   |   |-- run_florence_ingestion.py
|   |   |   |-- STREAMLIT_APP_README.md
|   |   |   |-- streamlit_chat_app.py
|   |   |   |-- supabase_utils.py
|   |   |   |-- synthesize_building_info.py
|   |   |   |-- test_florence2_detection.py
|   |   |   `-- upload_project_descriptions_to_supabase.py
|   |   |-- google/
|   |   |   |-- complete_results.json
|   |   |   |-- extract_structured_info_google.py
|   |   |   |-- generate_embeddings_gemini.py
|   |   |   |-- google_cloud_ocr_test.py
|   |   |   |-- ocr_results.json
|   |   |   `-- requirements.txt
|   |   |-- yolo_model/
|   |   |   `-- data.yaml
|   |   `-- .gitignore
|   `-- ExcelAgent/
|       `-- AI/
|           |-- backend/
|           |   |-- agents/
|           |   |   |-- __init__.py
|           |   |   |-- building_code_rag.py
|           |   |   |-- graphql_mcp_tool.py
|           |   |   `-- orchestrator.py
|           |   |-- Building codes/
|           |   |   |-- concrete/
|           |   |   |   |-- cleaned_chunks_output_concrete.txt
|           |   |   |   |-- CSA A23.3-14 - Design of Concrete Structures.pdf
|           |   |   |   |-- simple_embeddings.npy
|           |   |   |   |-- simple_metadata.pkl
|           |   |   |   `-- simple_summary.json
|           |   |   |-- obc/
|           |   |   |   |-- onc_chunks.json
|           |   |   |   |-- simple_embeddings (1).npy
|           |   |   |   |-- simple_metadata (1).pkl
|           |   |   |   `-- simple_summary (1).json
|           |   |   |-- steel/
|           |   |   |   |-- cleaned_chunks_output_steel.txt
|           |   |   |   |-- CSA.pdf
|           |   |   |   |-- simple_embeddings (2).npy
|           |   |   |   |-- simple_metadata (2).pkl
|           |   |   |   `-- simple_summary (2).json
|           |   |   `-- timber/
|           |   |       |-- annexA.txt
|           |   |       |-- annexB.txt
|           |   |       |-- clauses.txt
|           |   |       |-- simple_embeddings (3).npy
|           |   |       `-- simple_metadata (3).pkl
|           |   |-- api_server.py
|           |   |-- README.md
|           |   `-- requirements.txt
|           |-- SidOS/
|           |   |-- local_agent/
|           |   |   |-- __init__.py
|           |   |   |-- agent_service.py
|           |   |   |-- config.py
|           |   |   |-- excel_tools.py
|           |   |   `-- semantic_loader.py
|           |   |-- parsing/
|           |   |   |-- -o
|           |   |   |-- __init__.py
|           |   |   |-- build_semantic_knowledge_base.py
|           |   |   |-- CHATGPT_PROMPT.md
|           |   |   |-- clean_and_restructure_json.py
|           |   |   |-- COPY_PASTE_PROMPT.txt
|           |   |   |-- create_excel_tool_interface.py
|           |   |   |-- create_semantic_metadata.py
|           |   |   |-- EXCEL_DATA_EXTRACTION_GUIDE.md
|           |   |   |-- FIX_OPENPYXL_HANG.md
|           |   |   |-- Glulam_Column_metadata.json
|           |   |   |-- Glulam_Column_metadata_cleaned.json
|           |   |   |-- Glulam_Column_semantic_metadata.json
|           |   |   |-- Glulam_Column_tool_interface.json
|           |   |   |-- Glulam_Column_xlwings_extract.json
|           |   |   |-- Glulam_Column_xlwings_extract_v2.json
|           |   |   |-- glulam_knowledge_base.json
|           |   |   |-- intelligent_excel_parser.py
|           |   |   |-- LEGEND_DETECTION_FIXES.md
|           |   |   |-- metadata_converter.py
|           |   |   |-- parse_workbook.py
|           |   |   |-- parse_workbook_safe.sh
|           |   |   |-- README.md
|           |   |   |-- REFACTORING_SUMMARY.md
|           |   |   |-- requirements.txt
|           |   |   |-- SETUP.md
|           |   |   |-- test_openpyxl_import.py
|           |   |   |-- USAGE.md
|           |   |   `-- xlwings_excel_extractor.py
|           |   |-- semantic_metadata/
|           |   |   `-- examples/
|           |   |       `-- example_metadata.json
|           |   |-- tests/
|           |   |   `-- test_excel_tools.py
|           |   |-- NEXT_STEPS.md
|           |   |-- quick_test.py
|           |   |-- QUICKSTART.md
|           |   |-- README.md
|           |   |-- requirements.txt
|           |   `-- test_local_agent.py
|           |-- src/
|           |   |-- commands/
|           |   |   `-- commands.ts
|           |   |-- config/
|           |   |   `-- api.config.ts
|           |   `-- taskpane/
|           |       |-- taskpane.html
|           |       `-- taskpane.ts
|           |-- .gitignore
|           |-- explanation.txt
|           |-- GAMEPLAN_VERIFICATION.md
|           |-- manifest.xml
|           |-- package.json
|           |-- requirements.txt
|           |-- tsconfig.json
|           `-- webpack.config.js
|-- requirements/
|   |-- consolidated/
|   |   |-- INSTALLATION_GUIDE.md
|   |   |-- nodejs-all-dependencies.txt
|   |   |-- python-all-requirements.txt
|   |   `-- python-unique-requirements.txt
|   |-- docker/
|   |   `-- sandbox-GraphQL-MCP/
|   |       `-- Dockerfile
|   |-- nodejs/
|   |   |-- Frontend-Frontend/
|   |   |   `-- package.json
|   |   `-- Local-Agent-ExcelAgent-AI/
|   |       `-- package.json
|   |-- python/
|   |   |-- Backend/
|   |   |   `-- requirements.txt
|   |   |-- Frontend-backend/
|   |   |   `-- requirements.txt
|   |   |-- Local-Agent-dataprocessing-florence/
|   |   |   `-- requirements.txt
|   |   |-- Local-Agent-dataprocessing-florence-imageCHAT/
|   |   |   `-- requirements.txt
|   |   |-- Local-Agent-ExcelAgent-AI/
|   |   |   `-- requirements.txt
|   |   |-- Local-Agent-ExcelAgent-AI-backend/
|   |   |   `-- requirements.txt
|   |   |-- Local-Agent-ExcelAgent-AI-SidOS/
|   |   |   `-- requirements.txt
|   |   |-- Local-Agent-ExcelAgent-AI-SidOS-parsing/
|   |   |   `-- requirements.txt
|   |   `-- sandbox-GraphQL-MCP-fact-engine/
|   |       `-- requirements.txt
|   |-- INDEX.md
|   |-- README.md
|   `-- ROOT_VENV_SETUP.md
|-- sandbox/
|   |-- GraphQL-MCP/
|   |   |-- .github/
|   |   |   `-- workflows/
|   |   |       `-- docker.yml
|   |   |-- custom_tools/
|   |   |   |-- __init__.py
|   |   |   |-- ADD_TOOLS_TO_MCP.md
|   |   |   |-- base_tool.py
|   |   |   |-- building_perimeter_tool.py
|   |   |   |-- COMPOSABLE_TOOLS_GUIDE.md
|   |   |   |-- debug_model.py
|   |   |   |-- element_geometry_tool.py
|   |   |   |-- element_normalizer.py
|   |   |   |-- element_properties_tool.py
|   |   |   |-- element_relationships_tool.py
|   |   |   |-- explanation.txt
|   |   |   |-- find_beams_tool.py
|   |   |   |-- find_element_types_tool.py
|   |   |   |-- find_material_types_tool.py
|   |   |   |-- find_member_sections.py
|   |   |   |-- find_projects_by_material.py
|   |   |   |-- inspect_data_structure.py
|   |   |   |-- project_material_cache.py
|   |   |   |-- README.md
|   |   |   |-- test_composable_tools.py
|   |   |   |-- test_specific_model.py
|   |   |   |-- test_tools.py
|   |   |   `-- tool_registry.py
|   |   |-- dev/
|   |   |   |-- debug-client.ts
|   |   |   |-- debug-manual-client.ts
|   |   |   `-- graphql.ts
|   |   |-- fact_engine_service/
|   |   |   |-- composer/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- composer.py
|   |   |   |   `-- prompt.txt
|   |   |   |-- db/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- connection.py
|   |   |   |   |-- graphql_client.py
|   |   |   |   `-- queries.py
|   |   |   |-- executor/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- caching.py
|   |   |   |   |-- executor.py
|   |   |   |   `-- registry.py
|   |   |   |-- extractors/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- base.py
|   |   |   |   |-- element_type.py
|   |   |   |   |-- level.py
|   |   |   |   |-- material.py
|   |   |   |   |-- orientation.py
|   |   |   |   |-- project_summary.py
|   |   |   |   |-- section.py
|   |   |   |   `-- system_role.py
|   |   |   |-- models/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- answer.py
|   |   |   |   |-- fact_plan.py
|   |   |   |   `-- fact_result.py
|   |   |   |-- planner/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- planner.py
|   |   |   |   `-- prompt.txt
|   |   |   |-- utils/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- confidence.py
|   |   |   |   `-- speckle.py
|   |   |   |-- __init__.py
|   |   |   |-- check_logs.py
|   |   |   |-- check_setup.py
|   |   |   |-- config.py
|   |   |   |-- DEBUG_ISSUES.md
|   |   |   |-- FIX_INSTALL.md
|   |   |   |-- IMPLEMENTATION_NOTES.md
|   |   |   |-- INSTALL.md
|   |   |   |-- LOGGING_GUIDE.md
|   |   |   |-- main.py
|   |   |   |-- QUERY_PATTERN.md
|   |   |   |-- QUICK_START.md
|   |   |   |-- QUICK_TEST.md
|   |   |   |-- README.md
|   |   |   |-- requirements.txt
|   |   |   |-- SETUP.md
|   |   |   |-- START_HERE.md
|   |   |   |-- TEST_NOW.md
|   |   |   |-- test_service.py
|   |   |   `-- TESTING.md
|   |   |-- src/
|   |   |   |-- helpers/
|   |   |   |   |-- deprecation.ts
|   |   |   |   |-- headers.ts
|   |   |   |   |-- introspection.ts
|   |   |   |   `-- package.ts
|   |   |   `-- index.ts
|   |   |-- .dockerignore
|   |   |-- .gitattributes
|   |   |-- .gitignore
|   |   |-- .npmrc
|   |   |-- Dockerfile
|   |   |-- LICENSE
|   |   |-- raw_schema.graphql
|   |   |-- schema_analysis_output.txt
|   |   |-- schema_parser.py
|   |   |-- SCHEMA_PARSING_FIX.md
|   |   |-- smithery.yaml
|   |   |-- test_mcp_client.py
|   |   |-- test_natural_language.py
|   |   |-- test_natural_language_with_custom_tools.py
|   |   `-- test_schema_parser.py
|   |-- IFC-MCP/
|   |   |-- .cursor/
|   |   |   `-- mcp.json
|   |   `-- readrevit/
|   |       |-- forge-ifc-exporter/
|   |       |   |-- bundle/
|   |       |   |   `-- packageContents.xml
|   |       |   |-- src/
|   |       |   |   |-- Properties/
|   |       |   |   |   `-- AssemblyInfo.cs
|   |       |   |   |-- App.config
|   |       |   |   |-- IFCExport.csproj
|   |       |   |   `-- RevitCommand.cs
|   |       |   `-- README.md
|   |       |-- convert_all_rvt.py
|   |       |-- README.md
|   |       |-- run_aps_setup.py
|   |       |-- supabase_client.py
|   |       `-- supabase_setup.py
|   |-- oldagents/
|   |   |-- agents/
|   |   |   |-- agents/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- base_agent.py
|   |   |   |   |-- design_orchestrator.py
|   |   |   |   |-- draft_orchestrator.py
|   |   |   |   |-- search_orchestrator.py
|   |   |   |   |-- search_orchestratorr1.py
|   |   |   |   `-- team_orchestrator.py
|   |   |   |-- cognition/
|   |   |   |   |-- __init__.py
|   |   |   |   `-- planner.py
|   |   |   |-- core/
|   |   |   |   |-- execution_graphs/
|   |   |   |   |   |-- retrieve_db_info.graph.md
|   |   |   |   |   `-- written_work_analysis.graph.md
|   |   |   |   |-- planner/
|   |   |   |   |   |-- intent_catalog.md
|   |   |   |   |   `-- scenario_router.md
|   |   |   |   |-- plans/
|   |   |   |   |   |-- retrieve_db_info.plan.md
|   |   |   |   |   `-- written_work_improvement.plan.md
|   |   |   |   |-- runtime/
|   |   |   |   |   |-- ai_executor.py
|   |   |   |   |   |-- dry_run.py
|   |   |   |   |   |-- load_specs.py
|   |   |   |   |   `-- route_query.py
|   |   |   |   |-- scenarios/
|   |   |   |   |   |-- find_past_project.md
|   |   |   |   |   `-- rfp_response.md
|   |   |   |   `-- capability_registry.py
|   |   |   |-- execution/
|   |   |   |   |-- __init__.py
|   |   |   |   `-- trace.py
|   |   |   |-- tools/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- calculation_tools.py
|   |   |   |   `-- search_tools.py
|   |   |   |-- ARCHITECTURE_MULTI_AGENT.md
|   |   |   |-- demo_cache.json
|   |   |   |-- demo_cache.py
|   |   |   |-- explain.txt
|   |   |   `-- run_multi_agent.py
|   |   `-- backend/
|   |       |-- main.py
|   |       |-- README.md
|   |       |-- requirements.txt
|   |       |-- run.bat
|   |       |-- run.sh
|   |       `-- SETUP_COMPLETE.md
|   |-- skyciv-demo/
|   |   |-- backend/
|   |   |   |-- main.py
|   |   |   |-- requirements.txt
|   |   |   |-- run.sh
|   |   |   |-- skyciv_client.py
|   |   |   `-- test_skyciv_connection.py
|   |   |-- frontend/
|   |   |   |-- example-page.vue
|   |   |   |-- SkyCivViewer.vue
|   |   |   `-- useSkyCiv.ts
|   |   |-- models/
|   |   |   |-- script1.json
|   |   |   `-- script2.json
|   |   |-- INTEGRATION.md
|   |   `-- README.md
|   `-- supabaseQLquery/
|       `-- speckle_client.py
|-- Services/
|   `-- speckle-server/
|       |-- .cursor/
|       |   |-- rules/
|       |   |   |-- frontend-core.mdc
|       |   |   |-- graphql-patterns.mdc
|       |   |   |-- tailwind-design-system.mdc
|       |   |   `-- vue-patterns.mdc
|       |   `-- mcp.json
|       |-- .devcontainer/
|       |   |-- devcontainer.json
|       |   |-- docker-compose-devcontainer.yml
|       |   `-- postCreateCommand.sh
|       |-- .github/
|       |   |-- instructions/
|       |   |   |-- review-guide/
|       |   |   |   |-- frontend.instructions.md
|       |   |   |   |-- general.instructions.md
|       |   |   |   `-- server.instructions.md
|       |   |   |-- frontend-core.instructions.md
|       |   |   |-- graphql-patterns.instructions.md
|       |   |   |-- tailwind-design-system.instructions.md
|       |   |   `-- vue-patterns.instructions.md
|       |   |-- ISSUE_TEMPLATE/
|       |   |   |-- bug_report.md
|       |   |   `-- feature_request.md
|       |   |-- workflows/
|       |   |   |-- config/
|       |   |   |   `-- multiregion.test-ci.json
|       |   |   |-- scripts/
|       |   |   |   |-- common.sh
|       |   |   |   |-- get_chart_name.sh
|       |   |   |   |-- get_version.sh
|       |   |   |   |-- publish_cloudflare_pages.sh
|       |   |   |   |-- publish_fe2_sourcemaps.sh
|       |   |   |   `-- publish_helm_chart_oci.sh
|       |   |   |-- builds.yml
|       |   |   |-- close-issue.yml
|       |   |   |-- deployment-tests.yml
|       |   |   |-- get-chart-name.yml
|       |   |   |-- get-version.yml
|       |   |   |-- manual-trigger-test-deployment.yml
|       |   |   |-- npm.yml
|       |   |   |-- open-issue.yml
|       |   |   |-- publish.yml
|       |   |   |-- pull-request.yml
|       |   |   |-- release.yml
|       |   |   |-- snyk.yml
|       |   |   |-- tests.yml
|       |   |   `-- update-images.yml
|       |   |-- CODE_OF_CONDUCT.md
|       |   |-- codecov.yml
|       |   |-- CONTRIBUTING.md
|       |   `-- pull_request_template.md
|       |-- .husky/
|       |   |-- .gitignore
|       |   `-- pre-commit
|       |-- .yarn/
|       |   |-- releases/
|       |   |   `-- yarn-4.5.0.cjs
|       |   `-- versions/
|       |       `-- 9222c3ef.yml
|       |-- .zed/
|       |   `-- debug.json
|       |-- infrastructure/
|       |   |-- terraform/
|       |   |   |-- eks.tf
|       |   |   |-- outputs.tf
|       |   |   |-- rds.tf
|       |   |   |-- redis.tf
|       |   |   |-- s3.tf
|       |   |   |-- terraform.tfstate
|       |   |   |-- terraform.tfvars
|       |   |   |-- variables.tf
|       |   |   `-- vpc.tf
|       |   |-- build-and-push-server.ps1
|       |   |-- create-priority-classes.yaml
|       |   |-- delete-user.ps1
|       |   |-- DEPLOYMENT_GUIDE.md
|       |   |-- helm-values-aws.yaml
|       |   |-- PRODUCTION_SETUP.md
|       |   |-- rds-ca-bundle.pem
|       |   |-- setup-ecr-auth.ps1
|       |   `-- setup-kubernetes-secrets.ps1
|       |-- packages/
|       |   |-- ai-service/
|       |   |   |-- src/
|       |   |   |   |-- api/
|       |   |   |   |   |-- __init__.py
|       |   |   |   |   |-- main.py
|       |   |   |   |   `-- routes.py
|       |   |   |   |-- core/
|       |   |   |   |   |-- __init__.py
|       |   |   |   |   `-- config.py
|       |   |   |   `-- services/
|       |   |   |       |-- __init__.py
|       |   |   |       |-- chat.py
|       |   |   |       |-- openai_client.py
|       |   |   |       `-- speckle_client.py
|       |   |   |-- Dockerfile
|       |   |   |-- package.json
|       |   |   |-- README.md
|       |   |   `-- requirements.txt
|       |   |-- fileimport-service/
|       |   |   |-- bin/
|       |   |   |   `-- www.js
|       |   |   |-- scripts/
|       |   |   |   `-- downloadBlob.js
|       |   |   |-- src/
|       |   |   |   |-- clients/
|       |   |   |   |   `-- knex.ts
|       |   |   |   |-- common/
|       |   |   |   |   |-- output.ts
|       |   |   |   |   `-- processHandling.ts
|       |   |   |   |-- controller/
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- env.ts
|       |   |   |   |   |-- api.ts
|       |   |   |   |   |-- daemon.ts
|       |   |   |   |   |-- filesApi.ts
|       |   |   |   |   |-- objDependencies.ts
|       |   |   |   |   `-- prometheusMetrics.ts
|       |   |   |   |-- ifc/
|       |   |   |   |   |-- import_file.js
|       |   |   |   |   |-- index.js
|       |   |   |   |   |-- parser.js
|       |   |   |   |   |-- utils.js
|       |   |   |   |   `-- web-ifc.wasm
|       |   |   |   |-- ifc-dotnet/
|       |   |   |   |   |-- .config/
|       |   |   |   |   |   `-- dotnet-tools.json
|       |   |   |   |   |-- ifc-converter.csproj
|       |   |   |   |   |-- ifc-converter.sln
|       |   |   |   |   `-- Program.cs
|       |   |   |   |-- obj/
|       |   |   |   |   |-- samples/
|       |   |   |   |   |   `-- untitled.mtl
|       |   |   |   |   |-- import_file.py
|       |   |   |   |   |-- mtl_file_collection.py
|       |   |   |   |   `-- obj_file.py
|       |   |   |   |-- observability/
|       |   |   |   |   `-- logging.ts
|       |   |   |   |-- stl/
|       |   |   |   |   |-- samples/
|       |   |   |   |   |   `-- Gizmo_Spoon_Rider_bin.stl
|       |   |   |   |   `-- import_file.py
|       |   |   |   |-- aliasLoader.ts
|       |   |   |   |-- bin.ts
|       |   |   |   |-- bootstrap.ts
|       |   |   |   `-- root.ts
|       |   |   |-- .env.example
|       |   |   |-- Dockerfile
|       |   |   |-- eslint.config.mjs
|       |   |   |-- multiregion.example.json
|       |   |   |-- package.json
|       |   |   |-- README.md
|       |   |   |-- requirements.txt
|       |   |   |-- RUN_INSTRUCTIONS.md
|       |   |   |-- tsconfig.build.json
|       |   |   |-- tsconfig.json
|       |   |   `-- vitest.config.ts
|       |   |-- frontend-2/
|       |   |   |-- .cursor/
|       |   |   |   `-- rules/
|       |   |   |       `-- nuxt-patterns.mdc
|       |   |   |-- app/
|       |   |   |   `-- spa-loading-template.html
|       |   |   |-- assets/
|       |   |   |   |-- css/
|       |   |   |   |   |-- tailwind.css
|       |   |   |   |   `-- vtippy.css
|       |   |   |   `-- images/
|       |   |   |       |-- auth/
|       |   |   |       |   |-- github_icon.svg
|       |   |   |       |   |-- google_icon.svg
|       |   |   |       |   |-- google_icon_w_bg.svg
|       |   |   |       |   `-- ms_icon.svg
|       |   |   |       |-- connectors/
|       |   |   |       |   |-- hero_dark.webp
|       |   |   |       |   `-- hero_light.webp
|       |   |   |       `-- workspace/
|       |   |   |           `-- cubes.webp
|       |   |   |-- components/
|       |   |   |   |-- auth/
|       |   |   |   |   |-- sso/
|       |   |   |   |   |   |-- Login.vue
|       |   |   |   |   |   |-- Register.vue
|       |   |   |   |   |   `-- WorkspaceSelect.vue
|       |   |   |   |   |-- third-party/
|       |   |   |   |   |   |-- LoginBlock.vue
|       |   |   |   |   |   |-- LoginButtonBase.vue
|       |   |   |   |   |   |-- LoginButtonGithub.vue
|       |   |   |   |   |   |-- LoginButtonGoogle.vue
|       |   |   |   |   |   |-- LoginButtonMicrosoft.vue
|       |   |   |   |   |   `-- LoginButtonOIDC.vue
|       |   |   |   |   |-- LoginPanel.vue
|       |   |   |   |   |-- LoginWithEmailBlock.vue
|       |   |   |   |   |-- PasswordChecks.vue
|       |   |   |   |   |-- PasswordResetFinalizationPanel.vue
|       |   |   |   |   |-- PasswordResetPanel.vue
|       |   |   |   |   |-- RegisterNewsletter.vue
|       |   |   |   |   |-- RegisterPanel.vue
|       |   |   |   |   |-- RegisterTerms.vue
|       |   |   |   |   |-- RegisterWithEmailBlock.vue
|       |   |   |   |   `-- WorkspaceInviteHeader.vue
|       |   |   |   |-- automate/
|       |   |   |   |   |-- automation/
|       |   |   |   |   |   |-- create-dialog/
|       |   |   |   |   |   |   |-- AutomationDetailsStep.vue
|       |   |   |   |   |   |   |-- DoneStep.vue
|       |   |   |   |   |   |   |-- FunctionParametersStep.vue
|       |   |   |   |   |   |   `-- SelectFunctionStep.vue
|       |   |   |   |   |   `-- CreateDialog.vue
|       |   |   |   |   |-- function/
|       |   |   |   |   |   |-- create-dialog/
|       |   |   |   |   |   |   |-- AuthorizeStep.vue
|       |   |   |   |   |   |   |-- DetailsStep.vue
|       |   |   |   |   |   |   |-- DoneStep.vue
|       |   |   |   |   |   |   |-- TemplateCard.vue
|       |   |   |   |   |   |   `-- TemplateStep.vue
|       |   |   |   |   |   |-- page/
|       |   |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   |   |-- Info.vue
|       |   |   |   |   |   |   |-- InfoBlock.vue
|       |   |   |   |   |   |   `-- ParametersDialog.vue
|       |   |   |   |   |   |-- Card.vue
|       |   |   |   |   |   |-- CardView.vue
|       |   |   |   |   |   |-- CreateDialog.vue
|       |   |   |   |   |   |-- EditDialog.vue
|       |   |   |   |   |   `-- Logo.vue
|       |   |   |   |   |-- functions/
|       |   |   |   |   |   `-- page/
|       |   |   |   |   |       |-- Header.vue
|       |   |   |   |   |       `-- Items.vue
|       |   |   |   |   |-- runs/
|       |   |   |   |   |   |-- trigger-status/
|       |   |   |   |   |   |   |-- dialog/
|       |   |   |   |   |   |   |   |-- FunctionRun.vue
|       |   |   |   |   |   |   |   `-- RunsRows.vue
|       |   |   |   |   |   |   |-- Dialog.vue
|       |   |   |   |   |   |   `-- Icon.vue
|       |   |   |   |   |   |-- AttachmentButton.vue
|       |   |   |   |   |   |-- StatusBadge.vue
|       |   |   |   |   |   |-- Table.vue
|       |   |   |   |   |   `-- TriggerStatus.vue
|       |   |   |   |   `-- viewer/
|       |   |   |   |       |-- panel/
|       |   |   |   |       |   |-- FunctionRunRow.vue
|       |   |   |   |       |   `-- FunctionRunRowObjectResult.vue
|       |   |   |   |       `-- Panel.vue
|       |   |   |   |-- billing/
|       |   |   |   |   |-- Alert.vue
|       |   |   |   |   |-- TransitionCards.vue
|       |   |   |   |   `-- UsageAlert.vue
|       |   |   |   |-- common/
|       |   |   |   |   |-- editable/
|       |   |   |   |   |   |-- Description.vue
|       |   |   |   |   |   `-- Title.vue
|       |   |   |   |   |-- model/
|       |   |   |   |   |   `-- Select.vue
|       |   |   |   |   |-- prose/
|       |   |   |   |   |   |-- GithubReadme.vue
|       |   |   |   |   |   `-- MarkdownDescription.vue
|       |   |   |   |   |-- tiptap/
|       |   |   |   |   |   |-- MentionList.vue
|       |   |   |   |   |   |-- MentionListItem.vue
|       |   |   |   |   |   `-- TextEditor.vue
|       |   |   |   |   |-- Card.vue
|       |   |   |   |   |-- ClipboardInputWithToast.vue
|       |   |   |   |   |-- CodeOutput.vue
|       |   |   |   |   |-- ConfirmDialog.vue
|       |   |   |   |   |-- CopyButton.vue
|       |   |   |   |   |-- EditableTitleDescription.vue
|       |   |   |   |   |-- EmptySearchState.vue
|       |   |   |   |   |-- EmptyState.vue
|       |   |   |   |   |-- GenericEmptyState.vue
|       |   |   |   |   |-- Text.vue
|       |   |   |   |   |-- TitleDescription.vue
|       |   |   |   |   `-- TransitioningContents.vue
|       |   |   |   |-- connectors/
|       |   |   |   |   |-- Banner.vue
|       |   |   |   |   |-- Card.vue
|       |   |   |   |   `-- Page.vue
|       |   |   |   |-- dashboard/
|       |   |   |   |   |-- ProjectsSidebar.vue
|       |   |   |   |   |-- Sidebar.vue
|       |   |   |   |   `-- SpeckleConPromo.vue
|       |   |   |   |-- dashboards/
|       |   |   |   |   |-- share/
|       |   |   |   |   |   |-- Dialog.vue
|       |   |   |   |   |   `-- Share.vue
|       |   |   |   |   |-- Card.vue
|       |   |   |   |   |-- CreateDialog.vue
|       |   |   |   |   |-- EditDialog.vue
|       |   |   |   |   `-- List.vue
|       |   |   |   |-- error/
|       |   |   |   |   |-- page/
|       |   |   |   |   |   |-- GenericErrorBlock.vue
|       |   |   |   |   |   |-- GenericUnauthorizedBlock.vue
|       |   |   |   |   |   |-- ProjectAccessErrorBlock.vue
|       |   |   |   |   |   |-- ProjectInviteBanner.vue
|       |   |   |   |   |   |-- Renderer.vue
|       |   |   |   |   |   `-- WorkspaceAccessErrorBlock.vue
|       |   |   |   |   `-- Reference.vue
|       |   |   |   |-- file-viewers/
|       |   |   |   |   |-- ExcelViewer.vue
|       |   |   |   |   `-- PdfViewer.vue
|       |   |   |   |-- form/
|       |   |   |   |   |-- file-upload/
|       |   |   |   |   |   |-- Progress.vue
|       |   |   |   |   |   `-- ProgressRow.vue
|       |   |   |   |   |-- json/
|       |   |   |   |   |   |-- ArrayListElement.vue
|       |   |   |   |   |   |-- ArrayListRenderer.vue
|       |   |   |   |   |   |-- BooleanControlRenderer.vue
|       |   |   |   |   |   |-- DateControlRenderer.vue
|       |   |   |   |   |   |-- DateTimeControlRenderer.vue
|       |   |   |   |   |   |-- EnumControlRenderer.vue
|       |   |   |   |   |   |-- EnumOneOfControlRenderer.vue
|       |   |   |   |   |   |-- Form.vue
|       |   |   |   |   |   |-- IntegerControlRenderer.vue
|       |   |   |   |   |   |-- MultiStringControlRenderer.vue
|       |   |   |   |   |   |-- NumberControlRenderer.vue
|       |   |   |   |   |   |-- StringControlRenderer.vue
|       |   |   |   |   |   `-- TimeControlRenderer.vue
|       |   |   |   |   |-- select/
|       |   |   |   |   |   |-- automate/
|       |   |   |   |   |   |   `-- FunctionReleases.vue
|       |   |   |   |   |   |-- Models.vue
|       |   |   |   |   |   |-- ProjectRoles.vue
|       |   |   |   |   |   |-- Projects.vue
|       |   |   |   |   |   |-- SavedView.vue
|       |   |   |   |   |   |-- SavedViewGroup.vue
|       |   |   |   |   |   |-- SeatType.vue
|       |   |   |   |   |   |-- ServerRoles.vue
|       |   |   |   |   |   |-- Users.vue
|       |   |   |   |   |   |-- WorkspaceRoles.vue
|       |   |   |   |   |   `-- WorkspaceSeatType.vue
|       |   |   |   |   |-- ButtonSecondaryViewAll.vue
|       |   |   |   |   `-- MarkdownEditor.vue
|       |   |   |   |-- global/
|       |   |   |   |   |-- icon/
|       |   |   |   |   |   |-- viewer/
|       |   |   |   |   |   |   |-- CameraControls.vue
|       |   |   |   |   |   |   |-- Dev.vue
|       |   |   |   |   |   |   |-- Discussions.vue
|       |   |   |   |   |   |   |-- Explode.vue
|       |   |   |   |   |   |   |-- Explorer.vue
|       |   |   |   |   |   |   |-- Isolate.vue
|       |   |   |   |   |   |   |-- LightControls.vue
|       |   |   |   |   |   |   |-- Measurements.vue
|       |   |   |   |   |   |   |-- Models.vue
|       |   |   |   |   |   |   |-- SectionBox.vue
|       |   |   |   |   |   |   |-- Settings.vue
|       |   |   |   |   |   |   |-- Unisolate.vue
|       |   |   |   |   |   |   |-- ViewModes.vue
|       |   |   |   |   |   |   `-- Zoom.vue
|       |   |   |   |   |   |-- Account.vue
|       |   |   |   |   |   |-- Bolt.vue
|       |   |   |   |   |   |-- Calendar.vue
|       |   |   |   |   |   |-- Changelog.vue
|       |   |   |   |   |   |-- Check.vue
|       |   |   |   |   |   |-- CircleCheck.vue
|       |   |   |   |   |   |-- CircleExclamation.vue
|       |   |   |   |   |   |-- Colouring.vue
|       |   |   |   |   |   |-- ColouringOutline.vue
|       |   |   |   |   |   |-- Community.vue
|       |   |   |   |   |   |-- Connectors.vue
|       |   |   |   |   |   |-- Cursor.vue
|       |   |   |   |   |   |-- Discussions.vue
|       |   |   |   |   |   |-- Docs.vue
|       |   |   |   |   |   |-- Documentation.vue
|       |   |   |   |   |   |-- Edit.vue
|       |   |   |   |   |   |-- Explode.vue
|       |   |   |   |   |   |-- Eye.vue
|       |   |   |   |   |   |-- EyeClosed.vue
|       |   |   |   |   |   |-- Feedback.vue
|       |   |   |   |   |   |-- FileExplorer.vue
|       |   |   |   |   |   |-- FreeOrbit.vue
|       |   |   |   |   |   |-- HandRotate.vue
|       |   |   |   |   |   |-- HandSelect.vue
|       |   |   |   |   |   |-- HandZoom.vue
|       |   |   |   |   |   |-- Home.vue
|       |   |   |   |   |   |-- IconMeasureArea.vue
|       |   |   |   |   |   |-- IconMeasurePoint.vue
|       |   |   |   |   |   |-- Intercom.vue
|       |   |   |   |   |   |-- Measurements.vue
|       |   |   |   |   |   |-- MeasurePerpendicular.vue
|       |   |   |   |   |   |-- MeasurePointToPoint.vue
|       |   |   |   |   |   |-- Minus.vue
|       |   |   |   |   |   |-- MousePan.vue
|       |   |   |   |   |   |-- MouseRotate.vue
|       |   |   |   |   |   |-- MouseZoom.vue
|       |   |   |   |   |   |-- Notes.vue
|       |   |   |   |   |   |-- Perspective.vue
|       |   |   |   |   |   |-- PerspectiveMore.vue
|       |   |   |   |   |   |-- Play.vue
|       |   |   |   |   |   |-- Plus.vue
|       |   |   |   |   |   |-- Project.vue
|       |   |   |   |   |   |-- Projects.vue
|       |   |   |   |   |   |-- Server.vue
|       |   |   |   |   |   |-- Sidebar.vue
|       |   |   |   |   |   |-- SidebarClose.vue
|       |   |   |   |   |   |-- ThreeDots.vue
|       |   |   |   |   |   |-- Triangle.vue
|       |   |   |   |   |   |-- Tutorials.vue
|       |   |   |   |   |   |-- Versions.vue
|       |   |   |   |   |   |-- ViewModes.vue
|       |   |   |   |   |   |-- Views.vue
|       |   |   |   |   |   |-- Webhooks.vue
|       |   |   |   |   |   |-- Workspaces.vue
|       |   |   |   |   |   `-- XMark.vue
|       |   |   |   |   |-- illustration/
|       |   |   |   |   |   |-- emptystate/
|       |   |   |   |   |   |   |-- DiscussionTab.vue
|       |   |   |   |   |   |   |-- FiltersTab.vue
|       |   |   |   |   |   |   |-- Models.vue
|       |   |   |   |   |   |   |-- Project.vue
|       |   |   |   |   |   |   |-- ProjectTab.vue
|       |   |   |   |   |   |   |-- ViewsTab.vue
|       |   |   |   |   |   |   `-- Workspace.vue
|       |   |   |   |   |   `-- ProjectShape.vue
|       |   |   |   |   `-- HelpText.vue
|       |   |   |   |-- header/
|       |   |   |   |   |-- nav/
|       |   |   |   |   |   |-- notifications/
|       |   |   |   |   |   |   |-- Invite.vue
|       |   |   |   |   |   |   |-- Notifications.vue
|       |   |   |   |   |   |   |-- ProjectInvite.vue
|       |   |   |   |   |   |   `-- WorkspaceInvite.vue
|       |   |   |   |   |   |-- Bar.vue
|       |   |   |   |   |   |-- Link.vue
|       |   |   |   |   |   |-- Share.vue
|       |   |   |   |   |   `-- UserMenu.vue
|       |   |   |   |   |-- WorkspaceSwitcher/
|       |   |   |   |   |   |-- header/
|       |   |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   |   |-- Projects.vue
|       |   |   |   |   |   |   |-- SsoExpired.vue
|       |   |   |   |   |   |   `-- Workspace.vue
|       |   |   |   |   |   |-- List.vue
|       |   |   |   |   |   |-- ListItem.vue
|       |   |   |   |   |   `-- WorkspaceSwitcher.vue
|       |   |   |   |   |-- Empty.vue
|       |   |   |   |   |-- LogoBlock.vue
|       |   |   |   |   |-- ThemeToggle.vue
|       |   |   |   |   `-- WithEmptyPage.vue
|       |   |   |   |-- integrations/
|       |   |   |   |   `-- acc/
|       |   |   |   |       |-- actions/
|       |   |   |   |       |   `-- Menu.vue
|       |   |   |   |       |-- dialog/
|       |   |   |   |       |   `-- CreateSync.vue
|       |   |   |   |       |-- Card.vue
|       |   |   |   |       |-- FileSelector.vue
|       |   |   |   |       |-- FolderContents.vue
|       |   |   |   |       |-- FolderNode.vue
|       |   |   |   |       |-- Hubs.vue
|       |   |   |   |       |-- ModelItem.vue
|       |   |   |   |       |-- ModelSelector.vue
|       |   |   |   |       |-- Projects.vue
|       |   |   |   |       |-- Syncs.vue
|       |   |   |   |       |-- SyncStatus.vue
|       |   |   |   |       `-- SyncStatusModelItem.vue
|       |   |   |   |-- invite/
|       |   |   |   |   |-- dialog/
|       |   |   |   |   |   |-- project/
|       |   |   |   |   |   |   |-- Project.vue
|       |   |   |   |   |   |   `-- Row.vue
|       |   |   |   |   |   |-- shared/
|       |   |   |   |   |   |   `-- SelectUsers.vue
|       |   |   |   |   |   |-- workspace/
|       |   |   |   |   |   |   `-- SelectRole.vue
|       |   |   |   |   |   |-- CancelInvite.vue
|       |   |   |   |   |   |-- Server.vue
|       |   |   |   |   |   `-- Workspace.vue
|       |   |   |   |   `-- Banner.vue
|       |   |   |   |-- notifications/
|       |   |   |   |   `-- DashboardList.vue
|       |   |   |   |-- onboarding/
|       |   |   |   |   `-- questions/
|       |   |   |   |       |-- Form.vue
|       |   |   |   |       |-- PlanSelect.vue
|       |   |   |   |       |-- RoleSelect.vue
|       |   |   |   |       `-- SourceSelect.vue
|       |   |   |   |-- popups/
|       |   |   |   |   `-- SignIn.vue
|       |   |   |   |-- presentation/
|       |   |   |   |   |-- controls/
|       |   |   |   |   |   |-- Button.vue
|       |   |   |   |   |   `-- Controls.vue
|       |   |   |   |   |-- floatingPanel/
|       |   |   |   |   |   |-- Button.vue
|       |   |   |   |   |   `-- FloatingPanel.vue
|       |   |   |   |   |-- slideList/
|       |   |   |   |   |   |-- Slide.vue
|       |   |   |   |   |   `-- SlideList.vue
|       |   |   |   |   |-- state/
|       |   |   |   |   |   `-- Setup.vue
|       |   |   |   |   |-- viewer/
|       |   |   |   |   |   |-- PostSetup.vue
|       |   |   |   |   |   |-- Setup.vue
|       |   |   |   |   |   `-- Wrapper.vue
|       |   |   |   |   |-- Actions.vue
|       |   |   |   |   |-- Header.vue
|       |   |   |   |   |-- InfoSidebar.vue
|       |   |   |   |   |-- LeftSidebar.vue
|       |   |   |   |   |-- Loading.vue
|       |   |   |   |   |-- PageWrapper.vue
|       |   |   |   |   |-- ShareDialog.vue
|       |   |   |   |   |-- SlideEditDialog.vue
|       |   |   |   |   |-- SlideIndicator.vue
|       |   |   |   |   `-- SpeckleLogo.vue
|       |   |   |   |-- preview/
|       |   |   |   |   `-- Image.vue
|       |   |   |   |-- pricingTable/
|       |   |   |   |   |-- Addon.vue
|       |   |   |   |   |-- Plan.vue
|       |   |   |   |   |-- PlanFeature.vue
|       |   |   |   |   `-- PricingTable.vue
|       |   |   |   |-- project/
|       |   |   |   |   |-- model-page/
|       |   |   |   |   |   |-- dialog/
|       |   |   |   |   |   |   |-- embed/
|       |   |   |   |   |   |   |   |-- Embed.vue
|       |   |   |   |   |   |   |   `-- Iframe.vue
|       |   |   |   |   |   |   |-- move-to/
|       |   |   |   |   |   |   |   |-- ExistingTab.vue
|       |   |   |   |   |   |   |   `-- NewTab.vue
|       |   |   |   |   |   |   |-- Delete.vue
|       |   |   |   |   |   |   |-- EditMessage.vue
|       |   |   |   |   |   |   `-- MoveTo.vue
|       |   |   |   |   |   |-- versions/
|       |   |   |   |   |   |   |-- Card.vue
|       |   |   |   |   |   |   `-- CardActions.vue
|       |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   `-- Versions.vue
|       |   |   |   |   |-- models/
|       |   |   |   |   |   |-- Add.vue
|       |   |   |   |   |   `-- BasicCardView.vue
|       |   |   |   |   |-- page/
|       |   |   |   |   |   |-- automation/
|       |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   |-- Functions.vue
|       |   |   |   |   |   |   |-- FunctionSettingsDialog.vue
|       |   |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   |   |-- Models.vue
|       |   |   |   |   |   |   |-- Runs.vue
|       |   |   |   |   |   |   `-- TestAutomationInfo.vue
|       |   |   |   |   |   |-- automations/
|       |   |   |   |   |   |   |-- EmptyState.vue
|       |   |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   |   |-- Row.vue
|       |   |   |   |   |   |   |-- RunDialog.vue
|       |   |   |   |   |   |   `-- Tab.vue
|       |   |   |   |   |   |-- collaborators/
|       |   |   |   |   |   |   |-- generalAccess/
|       |   |   |   |   |   |   |   |-- Admins.vue
|       |   |   |   |   |   |   |   |-- GeneralAccess.vue
|       |   |   |   |   |   |   |   `-- Members.vue
|       |   |   |   |   |   |   |-- Collaborators.vue
|       |   |   |   |   |   |   `-- Row.vue
|       |   |   |   |   |   |-- dashboards/
|       |   |   |   |   |   |   `-- Dashboards.vue
|       |   |   |   |   |   |-- discussions/
|       |   |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   |   |-- Results.vue
|       |   |   |   |   |   |   `-- Tab.vue
|       |   |   |   |   |   |-- latest-items/
|       |   |   |   |   |   |   `-- comments/
|       |   |   |   |   |   |       |-- EmptyState.vue
|       |   |   |   |   |   |       |-- Grid.vue
|       |   |   |   |   |   |       |-- GridItem.vue
|       |   |   |   |   |   |       |-- List.vue
|       |   |   |   |   |   |       `-- ListItem.vue
|       |   |   |   |   |   |-- models/
|       |   |   |   |   |   |   |-- card/
|       |   |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   |   |-- EditDialog.vue
|       |   |   |   |   |   |   |   |-- RemoveSyncDialog.vue
|       |   |   |   |   |   |   |   `-- UpdatedTime.vue
|       |   |   |   |   |   |   |-- Actions.vue
|       |   |   |   |   |   |   |-- Card.vue
|       |   |   |   |   |   |   |-- CardView.vue
|       |   |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   |   |-- ListView.vue
|       |   |   |   |   |   |   |-- NewDialog.vue
|       |   |   |   |   |   |   |-- Results.vue
|       |   |   |   |   |   |   |-- StructureItem.vue
|       |   |   |   |   |   |   |-- Tab.vue
|       |   |   |   |   |   |   `-- UploadsDialog.vue
|       |   |   |   |   |   |-- settings/
|       |   |   |   |   |   |   |-- acc/
|       |   |   |   |   |   |   |   `-- Tab.vue
|       |   |   |   |   |   |   |-- general/
|       |   |   |   |   |   |   |   |-- block/
|       |   |   |   |   |   |   |   |   |-- Access/
|       |   |   |   |   |   |   |   |   |   |-- Access.vue
|       |   |   |   |   |   |   |   |   |   `-- Dialog.vue
|       |   |   |   |   |   |   |   |   |-- Delete/
|       |   |   |   |   |   |   |   |   |   `-- Delete.vue
|       |   |   |   |   |   |   |   |   |-- Leave/
|       |   |   |   |   |   |   |   |   |   |-- Dialog.vue
|       |   |   |   |   |   |   |   |   |   `-- Leave.vue
|       |   |   |   |   |   |   |   |   |-- Discussions.vue
|       |   |   |   |   |   |   |   |   `-- ProjectInfo.vue
|       |   |   |   |   |   |   |   `-- General.vue
|       |   |   |   |   |   |   |-- tokens/
|       |   |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   |   `-- Tokens.vue
|       |   |   |   |   |   |   |-- webhooks/
|       |   |   |   |   |   |   |   |-- CreateOrEditDialog.vue
|       |   |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   |   |-- EmptyState.vue
|       |   |   |   |   |   |   |   `-- Webhooks.vue
|       |   |   |   |   |   |   `-- Block.vue
|       |   |   |   |   |   |-- team/
|       |   |   |   |   |   |   |-- dialog/
|       |   |   |   |   |   |   |   `-- ManagePermissions.vue
|       |   |   |   |   |   |   |-- AccessSelect.vue
|       |   |   |   |   |   |   `-- PermissionSelect.vue
|       |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   `-- LatestItems.vue
|       |   |   |   |   |-- CardImportFileArea.vue
|       |   |   |   |   |-- CommentPermissionsSelect.vue
|       |   |   |   |   |-- EmptyState.vue
|       |   |   |   |   |-- InviteAdd.vue
|       |   |   |   |   |-- PendingFileImportStatus.vue
|       |   |   |   |   `-- VisibilitySelect.vue
|       |   |   |   |-- projects/
|       |   |   |   |   |-- add-dialog/
|       |   |   |   |   |   |-- Metadata.vue
|       |   |   |   |   |   `-- Workspace.vue
|       |   |   |   |   |-- invite/
|       |   |   |   |   |   `-- Banner.vue
|       |   |   |   |   |-- Add.vue
|       |   |   |   |   |-- AddDialog.vue
|       |   |   |   |   |-- Dashboard.vue
|       |   |   |   |   |-- DashboardEmptyState.vue
|       |   |   |   |   |-- DashboardEmptyStatePanel.vue
|       |   |   |   |   |-- DashboardFilled.vue
|       |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |-- HiddenProjectWarning.vue
|       |   |   |   |   |-- MoveToWorkspaceAlert.vue
|       |   |   |   |   |-- ProjectDashboardCard.vue
|       |   |   |   |   `-- WorkspaceSelect.vue
|       |   |   |   |-- settings/
|       |   |   |   |   |-- server/
|       |   |   |   |   |   |-- general/
|       |   |   |   |   |   |   `-- Version.vue
|       |   |   |   |   |   |-- regions/
|       |   |   |   |   |   |   |-- AddEditDialog.vue
|       |   |   |   |   |   |   |-- KeySelect.vue
|       |   |   |   |   |   |   `-- Table.vue
|       |   |   |   |   |   |-- user/
|       |   |   |   |   |   |   |-- ChangeRoleDialog.vue
|       |   |   |   |   |   |   `-- DeleteDialog.vue
|       |   |   |   |   |   |-- ActiveUsers.vue
|       |   |   |   |   |   `-- PendingInvitations.vue
|       |   |   |   |   |-- shared/
|       |   |   |   |   |   `-- projects/
|       |   |   |   |   |       `-- index.vue
|       |   |   |   |   |-- user/
|       |   |   |   |   |   |-- developer/
|       |   |   |   |   |   |   |-- AccessTokens/
|       |   |   |   |   |   |   |   |-- AccessTokens.vue
|       |   |   |   |   |   |   |   |-- CreateDialog.vue
|       |   |   |   |   |   |   |   `-- SuccessDialog.vue
|       |   |   |   |   |   |   |-- Applications/
|       |   |   |   |   |   |   |   |-- Applications.vue
|       |   |   |   |   |   |   |   |-- CreateEditDialog.vue
|       |   |   |   |   |   |   |   |-- RevealSecretDialog.vue
|       |   |   |   |   |   |   |   `-- SuccessDialog.vue
|       |   |   |   |   |   |   |-- AuthorizedApps.vue
|       |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   `-- Developer.vue
|       |   |   |   |   |   |-- email/
|       |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   |-- List.vue
|       |   |   |   |   |   |   |-- ListItem.vue
|       |   |   |   |   |   |   `-- SetPrimaryDialog.vue
|       |   |   |   |   |   `-- profile/
|       |   |   |   |   |       |-- ChangePassword.vue
|       |   |   |   |   |       |-- DeleteAccount.vue
|       |   |   |   |   |       |-- DeleteAccountDialog.vue
|       |   |   |   |   |       |-- Details.vue
|       |   |   |   |   |       `-- EditAvatar.vue
|       |   |   |   |   |-- workspaces/
|       |   |   |   |   |   |-- automation/
|       |   |   |   |   |   |   `-- Functions/
|       |   |   |   |   |   |       |-- Functions.vue
|       |   |   |   |   |   |       |-- RegenerateTokenDialog.vue
|       |   |   |   |   |   |       `-- TableRowActions.vue
|       |   |   |   |   |   |-- billing/
|       |   |   |   |   |   |   |-- addOns/
|       |   |   |   |   |   |   |   |-- AddOns.vue
|       |   |   |   |   |   |   |   `-- Card.vue
|       |   |   |   |   |   |   |-- upgradeDialog/
|       |   |   |   |   |   |   |   |-- SelectAddOn.vue
|       |   |   |   |   |   |   |   |-- Summary.vue
|       |   |   |   |   |   |   |   `-- UpgradeDialog.vue
|       |   |   |   |   |   |   |-- Page.vue
|       |   |   |   |   |   |   |-- Summary.vue
|       |   |   |   |   |   |   `-- Usage.vue
|       |   |   |   |   |   |-- General/
|       |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   |-- EditAvatar.vue
|       |   |   |   |   |   |   |-- EditSlugDialog.vue
|       |   |   |   |   |   |   `-- LeaveDialog.vue
|       |   |   |   |   |   |-- members/
|       |   |   |   |   |   |   |-- actions/
|       |   |   |   |   |   |   |   |-- Menu.vue
|       |   |   |   |   |   |   |   |-- ProjectPermissionsDialog.vue
|       |   |   |   |   |   |   |   |-- RemoveFromWorkspaceDialog.vue
|       |   |   |   |   |   |   |   |-- SeatTransitionCards.vue
|       |   |   |   |   |   |   |   |-- UpdateAdminDialog.vue
|       |   |   |   |   |   |   |   |-- UpdateRoleDialog.vue
|       |   |   |   |   |   |   |   `-- UpdateSeatTypeDialog.vue
|       |   |   |   |   |   |   |-- GuestsTable.vue
|       |   |   |   |   |   |   |-- InvitesTable.vue
|       |   |   |   |   |   |   |-- JoinRequestsTable.vue
|       |   |   |   |   |   |   |-- MembersTable.vue
|       |   |   |   |   |   |   |-- TableHeader.vue
|       |   |   |   |   |   |   `-- TableSeatType.vue
|       |   |   |   |   |   |-- regions/
|       |   |   |   |   |   |   `-- Select.vue
|       |   |   |   |   |   `-- security/
|       |   |   |   |   |       |-- sso/
|       |   |   |   |   |       |   |-- DeleteDialog.vue
|       |   |   |   |   |       |   |-- Form.vue
|       |   |   |   |   |       |   `-- Wrapper.vue
|       |   |   |   |   |       |-- DefaultSeat.vue
|       |   |   |   |   |       |-- Discoverability.vue
|       |   |   |   |   |       |-- DomainManagement.vue
|       |   |   |   |   |       |-- DomainProtection.vue
|       |   |   |   |   |       |-- DomainRemoveDialog.vue
|       |   |   |   |   |       `-- WorkspaceCreation.vue
|       |   |   |   |   |-- ConfirmDialog.vue
|       |   |   |   |   |-- SectionHeader.vue
|       |   |   |   |   `-- Sidebar.vue
|       |   |   |   |-- singleton/
|       |   |   |   |   |-- AppErrorStateManager.vue
|       |   |   |   |   |-- FileUploadErrorDialog.vue
|       |   |   |   |   |-- Managers.vue
|       |   |   |   |   `-- ToastManager.vue
|       |   |   |   |-- tutorials/
|       |   |   |   |   |-- Card.vue
|       |   |   |   |   `-- Page.vue
|       |   |   |   |-- viewer/
|       |   |   |   |   |-- anchored-point/
|       |   |   |   |   |   |-- thread/
|       |   |   |   |   |   |   |-- Comment.vue
|       |   |   |   |   |   |   |-- CommentAttachments.vue
|       |   |   |   |   |   |   `-- NewReply.vue
|       |   |   |   |   |   |-- NewThread.vue
|       |   |   |   |   |   |-- Thread.vue
|       |   |   |   |   |   `-- User.vue
|       |   |   |   |   |-- button-group/
|       |   |   |   |   |   |-- Button.vue
|       |   |   |   |   |   `-- ButtonGroup.vue
|       |   |   |   |   |-- camera/
|       |   |   |   |   |   `-- Menu.vue
|       |   |   |   |   |-- comments/
|       |   |   |   |   |   |-- Editor.vue
|       |   |   |   |   |   |-- ListItem.vue
|       |   |   |   |   |   |-- Panel.vue
|       |   |   |   |   |   `-- PortalOrDiv.vue
|       |   |   |   |   |-- compare-changes/
|       |   |   |   |   |   |-- ObjectGroup.vue
|       |   |   |   |   |   |-- Panel.vue
|       |   |   |   |   |   `-- Version.vue
|       |   |   |   |   |-- contextMenu/
|       |   |   |   |   |   `-- ContextMenu.vue
|       |   |   |   |   |-- controls/
|       |   |   |   |   |   |-- Bottom.vue
|       |   |   |   |   |   |-- ButtonGroup.vue
|       |   |   |   |   |   |-- ButtonToggle.vue
|       |   |   |   |   |   |-- Left.vue
|       |   |   |   |   |   `-- Right.vue
|       |   |   |   |   |-- dataviewer/
|       |   |   |   |   |   |-- Object.vue
|       |   |   |   |   |   |-- Panel.vue
|       |   |   |   |   |   `-- Row.vue
|       |   |   |   |   |-- embed/
|       |   |   |   |   |   |-- Footer.vue
|       |   |   |   |   |   `-- ManualLoad.vue
|       |   |   |   |   |-- explode/
|       |   |   |   |   |   `-- Menu.vue
|       |   |   |   |   |-- explorer/
|       |   |   |   |   |   `-- NavbarLink.vue
|       |   |   |   |   |-- filters/
|       |   |   |   |   |   |-- filter/
|       |   |   |   |   |   |   |-- boolean/
|       |   |   |   |   |   |   |   `-- Boolean.vue
|       |   |   |   |   |   |   |-- numeric/
|       |   |   |   |   |   |   |   |-- Between.vue
|       |   |   |   |   |   |   |   |-- Numeric.vue
|       |   |   |   |   |   |   |   `-- Single.vue
|       |   |   |   |   |   |   |-- string/
|       |   |   |   |   |   |   |   |-- Checkboxes.vue
|       |   |   |   |   |   |   |   |-- SelectAll.vue
|       |   |   |   |   |   |   |   |-- SortButton.vue
|       |   |   |   |   |   |   |   |-- String.vue
|       |   |   |   |   |   |   |   `-- ValueItem.vue
|       |   |   |   |   |   |   |-- Card.vue
|       |   |   |   |   |   |   |-- ConditionSelector.vue
|       |   |   |   |   |   |   |-- EmptyState.vue
|       |   |   |   |   |   |   |-- ExistenceCount.vue
|       |   |   |   |   |   |   `-- Header.vue
|       |   |   |   |   |   |-- property-selection/
|       |   |   |   |   |   |   |-- Header.vue
|       |   |   |   |   |   |   |-- Item.vue
|       |   |   |   |   |   |   |-- Panel.vue
|       |   |   |   |   |   |   `-- Search.vue
|       |   |   |   |   |   |-- LargePropertyWarningDialog.vue
|       |   |   |   |   |   |-- LogicSelector.vue
|       |   |   |   |   |   `-- Panel.vue
|       |   |   |   |   |-- layout/
|       |   |   |   |   |   |-- Panel.vue
|       |   |   |   |   |   `-- SidePanel.vue
|       |   |   |   |   |-- lightControls/
|       |   |   |   |   |   `-- Menu.vue
|       |   |   |   |   |-- limits/
|       |   |   |   |   |   |-- Dialog.vue
|       |   |   |   |   |   `-- WorkspaceDialog.vue
|       |   |   |   |   |-- measurements/
|       |   |   |   |   |   |-- Menu.vue
|       |   |   |   |   |   `-- UnitSelect.vue
|       |   |   |   |   |-- menu/
|       |   |   |   |   |   |-- Item.vue
|       |   |   |   |   |   |-- Menu.vue
|       |   |   |   |   |   `-- Panel.vue
|       |   |   |   |   |-- models/
|       |   |   |   |   |   |-- add/
|       |   |   |   |   |   |   |-- Dialog.vue
|       |   |   |   |   |   |   |-- ModelTab.vue
|       |   |   |   |   |   |   `-- ObjectTab.vue
|       |   |   |   |   |   |-- versions/
|       |   |   |   |   |   |   |-- ActiveCard.vue
|       |   |   |   |   |   |   |-- Card.vue
|       |   |   |   |   |   |   `-- Versions.vue
|       |   |   |   |   |   |-- Actions.vue
|       |   |   |   |   |   |-- Card.vue
|       |   |   |   |   |   |-- DetachedObjectCard.vue
|       |   |   |   |   |   |-- DetachedObjectHeader.vue
|       |   |   |   |   |   |-- Panel.vue
|       |   |   |   |   |   `-- VirtualTreeItem.vue
|       |   |   |   |   |-- resources/
|       |   |   |   |   |   |-- LimitAlert.vue
|       |   |   |   |   |   |-- ObjectCard.vue
|       |   |   |   |   |   |-- PersonalLimitAlert.vue
|       |   |   |   |   |   |-- UpgradeLimitAlert.vue
|       |   |   |   |   |   `-- VersionCard.vue
|       |   |   |   |   |-- saved-views/
|       |   |   |   |   |   |-- panel/
|       |   |   |   |   |   |   |-- groups/
|       |   |   |   |   |   |   |   `-- CreateDialog.vue
|       |   |   |   |   |   |   |-- view/
|       |   |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   |   |-- EditDialog.vue
|       |   |   |   |   |   |   |   `-- MoveDialog.vue
|       |   |   |   |   |   |   |-- views/
|       |   |   |   |   |   |   |   |-- group/
|       |   |   |   |   |   |   |   |   |-- DeleteDialog.vue
|       |   |   |   |   |   |   |   |   `-- Inner.vue
|       |   |   |   |   |   |   |   |-- EmptyState.vue
|       |   |   |   |   |   |   |   `-- Group.vue
|       |   |   |   |   |   |   |-- Groups.vue
|       |   |   |   |   |   |   `-- View.vue
|       |   |   |   |   |   `-- Panel.vue
|       |   |   |   |   |-- selection/
|       |   |   |   |   |   |-- KeyValuePair.vue
|       |   |   |   |   |   |-- Object.vue
|       |   |   |   |   |   |-- Sidebar.vue
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- settings/
|       |   |   |   |   |   `-- Menu.vue
|       |   |   |   |   |-- view-modes/
|       |   |   |   |   |   `-- Menu.vue
|       |   |   |   |   |-- AnchoredPoints.vue
|       |   |   |   |   |-- Base.vue
|       |   |   |   |   |-- CoreSetup.vue
|       |   |   |   |   |-- ExpansionTriangle.vue
|       |   |   |   |   |-- GlobalFilterReset.vue
|       |   |   |   |   |-- GlobalIsolationHiddenReset.vue
|       |   |   |   |   |-- IsolateButton.vue
|       |   |   |   |   |-- LoadingBar.vue
|       |   |   |   |   |-- PageSetup.vue
|       |   |   |   |   |-- PageWrapper.vue
|       |   |   |   |   |-- Scope.vue
|       |   |   |   |   |-- SearchInput.vue
|       |   |   |   |   |-- Sidebar.vue
|       |   |   |   |   |-- StatePostSetup.vue
|       |   |   |   |   |-- StateSetup.vue
|       |   |   |   |   |-- Tip.vue
|       |   |   |   |   `-- VisibilityButton.vue
|       |   |   |   `-- workspace/
|       |   |   |       |-- dashboard/
|       |   |   |       |   |-- Dashboard.vue
|       |   |   |       |   |-- Header.vue
|       |   |   |       |   `-- ProjectList.vue
|       |   |   |       |-- discoverableWorkspaces/
|       |   |   |       |   |-- Card.vue
|       |   |   |       |   `-- Modal.vue
|       |   |   |       |-- header/
|       |   |   |       |   `-- Actions.vue
|       |   |   |       |-- invite/
|       |   |   |       |   |-- Banner.vue
|       |   |   |       |   |-- Block.vue
|       |   |   |       |   |-- Card.vue
|       |   |   |       |   |-- DiscoverableWorkspaceBanner.vue
|       |   |   |       |   `-- Wrapper.vue
|       |   |   |       |-- joinRequest/
|       |   |   |       |   `-- ApproveDialog.vue
|       |   |   |       |-- moveProject/
|       |   |   |       |   |-- Confirm.vue
|       |   |   |       |   |-- index.vue
|       |   |   |       |   |-- Intro.vue
|       |   |   |       |   |-- Manager.vue
|       |   |   |       |   |-- SelectProject.vue
|       |   |   |       |   `-- SelectWorkspace.vue
|       |   |   |       |-- plan/
|       |   |   |       |   |-- LimitReachedDialog.vue
|       |   |   |       |   `-- ProjectModelLimitReachedDialog.vue
|       |   |   |       |-- sidebar/
|       |   |   |       |   |-- About.vue
|       |   |   |       |   |-- FreePlanAlert.vue
|       |   |   |       |   |-- Members.vue
|       |   |   |       |   |-- Security.vue
|       |   |   |       |   `-- Sidebar.vue
|       |   |   |       |-- wizard/
|       |   |   |       |   |-- step/
|       |   |   |       |   |   |-- AddOns.vue
|       |   |   |       |   |   |-- Details.vue
|       |   |   |       |   |   |-- Invites.vue
|       |   |   |       |   |   |-- Pricing.vue
|       |   |   |       |   |   |-- Region.vue
|       |   |   |       |   |   `-- Step.vue
|       |   |   |       |   |-- CancelDialog.vue
|       |   |   |       |   `-- Wizard.vue
|       |   |   |       |-- AdditionalSeatsChargeDisclaimer.vue
|       |   |   |       |-- AddProjectMenu.vue
|       |   |   |       |-- Avatar.vue
|       |   |   |       |-- Card.vue
|       |   |   |       |-- CreatePage.vue
|       |   |   |       |-- ExplainerVideoDialog.vue
|       |   |   |       |-- JoinPage.vue
|       |   |   |       |-- PermissionSelect.vue
|       |   |   |       `-- RegionStaticDataDisclaimer.vue
|       |   |   |-- composables/
|       |   |   |   |-- browser.ts
|       |   |   |   |-- cache.ts
|       |   |   |   |-- dates.ts
|       |   |   |   |-- debugging.ts
|       |   |   |   |-- env.ts
|       |   |   |   |-- globals.ts
|       |   |   |   |-- logging.ts
|       |   |   |   |-- routing.ts
|       |   |   |   `-- tooltips.ts
|       |   |   |-- layouts/
|       |   |   |   |-- dashboard.vue
|       |   |   |   |-- default.vue
|       |   |   |   |-- empty.vue
|       |   |   |   |-- landing.vue
|       |   |   |   |-- loginOrRegister.vue
|       |   |   |   |-- settings.vue
|       |   |   |   |-- viewer.vue
|       |   |   |   `-- withRightSidebar.vue
|       |   |   |-- lib/
|       |   |   |   |-- acc/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- useAccAuthManager.ts
|       |   |   |   |   |   |-- useAccFiles.ts
|       |   |   |   |   |   |-- useAccFolderData.ts
|       |   |   |   |   |   |-- useAccUser.ts
|       |   |   |   |   |   |-- useCreateAccSyncItem.ts
|       |   |   |   |   |   |-- useDeleteAccSyncItem.ts
|       |   |   |   |   |   `-- useUpdateAccSyncItem.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- fragments.ts
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   |-- queries.ts
|       |   |   |   |   |   `-- subscriptions.ts
|       |   |   |   |   `-- types.ts
|       |   |   |   |-- auth/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- activeUser.ts
|       |   |   |   |   |   |-- auth.ts
|       |   |   |   |   |   |-- onboarding.ts
|       |   |   |   |   |   |-- passwordReset.ts
|       |   |   |   |   |   `-- postAuthRedirect.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- errors.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- fragments.ts
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- checkBlockedDomain.ts
|       |   |   |   |   |   |-- onboarding.ts
|       |   |   |   |   |   |-- strategies.ts
|       |   |   |   |   |   `-- validation.ts
|       |   |   |   |   `-- services/
|       |   |   |   |       |-- auth.ts
|       |   |   |   |       `-- resetPassword.ts
|       |   |   |   |-- automate/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- automations.ts
|       |   |   |   |   |   |-- github.ts
|       |   |   |   |   |   |-- jsonSchema.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- runs.ts
|       |   |   |   |   |   `-- runStatus.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- automations.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- fragments.ts
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       |-- automations.ts
|       |   |   |   |       |-- functions.ts
|       |   |   |   |       `-- jsonSchema.ts
|       |   |   |   |-- billing/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- actions.ts
|       |   |   |   |   |   `-- prices.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   `-- mutations.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       `-- plan.ts
|       |   |   |   |-- common/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- async.ts
|       |   |   |   |   |   |-- crypto.ts
|       |   |   |   |   |   |-- datetime.ts
|       |   |   |   |   |   |-- dialog.ts
|       |   |   |   |   |   |-- dom.ts
|       |   |   |   |   |   |-- env.ts
|       |   |   |   |   |   |-- graphql.ts
|       |   |   |   |   |   |-- markdown.ts
|       |   |   |   |   |   |-- permissions.ts
|       |   |   |   |   |   |-- reactiveCookie.ts
|       |   |   |   |   |   |-- scopedState.ts
|       |   |   |   |   |   |-- serverInfo.ts
|       |   |   |   |   |   |-- singleton.ts
|       |   |   |   |   |   |-- toast.ts
|       |   |   |   |   |   |-- url.ts
|       |   |   |   |   |   `-- window.ts
|       |   |   |   |   |-- generated/
|       |   |   |   |   |   `-- gql/
|       |   |   |   |   |       |-- gql.ts
|       |   |   |   |   |       |-- graphql.ts
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- constants.ts
|       |   |   |   |   |   |-- debugging.ts
|       |   |   |   |   |   |-- dom.ts
|       |   |   |   |   |   |-- encodeDecode.ts
|       |   |   |   |   |   |-- error.ts
|       |   |   |   |   |   |-- github.ts
|       |   |   |   |   |   |-- graphql.ts
|       |   |   |   |   |   |-- mp.ts
|       |   |   |   |   |   |-- navigation.ts
|       |   |   |   |   |   |-- permissions.ts
|       |   |   |   |   |   |-- promise.ts
|       |   |   |   |   |   |-- random.ts
|       |   |   |   |   |   |-- resources.ts
|       |   |   |   |   |   |-- roles.ts
|       |   |   |   |   |   |-- route.ts
|       |   |   |   |   |   |-- tailwind.ts
|       |   |   |   |   |   |-- tiptap.ts
|       |   |   |   |   |   |-- type.ts
|       |   |   |   |   |   |-- utils.ts
|       |   |   |   |   |   `-- validation.ts
|       |   |   |   |   `-- utils/
|       |   |   |   |       |-- requests.ts
|       |   |   |   |       `-- tweetnacl.ts
|       |   |   |   |-- core/
|       |   |   |   |   |-- api/
|       |   |   |   |   |   |-- blobStorage.ts
|       |   |   |   |   |   `-- fileImport.ts
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   |-- mp.ts
|       |   |   |   |   |   `-- mpServer.ts
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- error.ts
|       |   |   |   |   |   |-- eventBus.ts
|       |   |   |   |   |   |-- fileImport.ts
|       |   |   |   |   |   |-- fileUpload.ts
|       |   |   |   |   |   |-- mp.ts
|       |   |   |   |   |   |-- navigation.ts
|       |   |   |   |   |   |-- server.ts
|       |   |   |   |   |   `-- theme.ts
|       |   |   |   |   |-- configs/
|       |   |   |   |   |   `-- apollo.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- base.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- apolloSetup.ts
|       |   |   |   |   |   |-- file.ts
|       |   |   |   |   |   |-- middleware.ts
|       |   |   |   |   |   |-- observability.ts
|       |   |   |   |   |   `-- redis.ts
|       |   |   |   |   |-- nuxt-modules/
|       |   |   |   |   |   `-- apollo/
|       |   |   |   |   |       |-- templates/
|       |   |   |   |   |       |   `-- plugin.ts
|       |   |   |   |   |       `-- module.ts
|       |   |   |   |   `-- tiptap/
|       |   |   |   |       |-- editorStateExtension.ts
|       |   |   |   |       |-- emailMentionExtension.ts
|       |   |   |   |       `-- mentionExtension.ts
|       |   |   |   |-- dashboard/
|       |   |   |   |   `-- helpers/
|       |   |   |   |       |-- connectors.ts
|       |   |   |   |       |-- tutorials.ts
|       |   |   |   |       |-- types.ts
|       |   |   |   |       `-- utils.ts
|       |   |   |   |-- dashboards/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- embed.ts
|       |   |   |   |   |   `-- management.ts
|       |   |   |   |   `-- graphql/
|       |   |   |   |       |-- mutations.ts
|       |   |   |   |       `-- queries.ts
|       |   |   |   |-- developer-settings/
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       `-- types.ts
|       |   |   |   |-- form/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- fileUpload.ts
|       |   |   |   |   |   |-- jsonRenderers.ts
|       |   |   |   |   |   |-- select.ts
|       |   |   |   |   |   |-- steps.ts
|       |   |   |   |   |   `-- textInput.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- fileUpload.ts
|       |   |   |   |   `-- jsonRenderers.ts
|       |   |   |   |-- global/
|       |   |   |   |   `-- helpers/
|       |   |   |   |       `-- components.ts
|       |   |   |   |-- integrations/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   `-- useAccIntegration.ts
|       |   |   |   |   `-- types.ts
|       |   |   |   |-- intercom/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   `-- enabled.ts
|       |   |   |   |   `-- graphql/
|       |   |   |   |       `-- queries.ts
|       |   |   |   |-- invites/
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       |-- constants.ts
|       |   |   |   |       |-- helpers.ts
|       |   |   |   |       |-- types.ts
|       |   |   |   |       `-- validation.ts
|       |   |   |   |-- layout/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   `-- resize.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       `-- components.ts
|       |   |   |   |-- multiregion/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- main.ts
|       |   |   |   |   |   `-- management.ts
|       |   |   |   |   `-- graphql/
|       |   |   |   |       `-- mutations.ts
|       |   |   |   |-- navigation/
|       |   |   |   |   `-- graphql/
|       |   |   |   |       `-- queries.ts
|       |   |   |   |-- object-sidebar/
|       |   |   |   |   `-- helpers.ts
|       |   |   |   |-- onboarding/
|       |   |   |   |   `-- helpers/
|       |   |   |   |       `-- types.ts
|       |   |   |   |-- presentations/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- mangament.ts
|       |   |   |   |   |   |-- setup.ts
|       |   |   |   |   |   |-- utils.ts
|       |   |   |   |   |   `-- viewerPostSetup.ts
|       |   |   |   |   `-- graphql/
|       |   |   |   |       |-- mutations.ts
|       |   |   |   |       `-- queries.ts
|       |   |   |   |-- projects/
|       |   |   |   |   |-- assets/
|       |   |   |   |   |   `-- dashed-border.svg
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- automationManagement.ts
|       |   |   |   |   |   |-- invites.ts
|       |   |   |   |   |   |-- modelManagement.ts
|       |   |   |   |   |   |-- models.ts
|       |   |   |   |   |   |-- permissions.ts
|       |   |   |   |   |   |-- previewImage.ts
|       |   |   |   |   |   |-- projectManagement.ts
|       |   |   |   |   |   |-- projectPages.ts
|       |   |   |   |   |   |-- team.ts
|       |   |   |   |   |   |-- tokenManagement.ts
|       |   |   |   |   |   |-- versionManagement.ts
|       |   |   |   |   |   `-- webhooks.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- fragments.ts
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   |-- queries.ts
|       |   |   |   |   |   `-- subscriptions.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       |-- components.ts
|       |   |   |   |       |-- limits.ts
|       |   |   |   |       |-- models.ts
|       |   |   |   |       |-- permissions.ts
|       |   |   |   |       |-- types.ts
|       |   |   |   |       `-- visibility.ts
|       |   |   |   |-- promo-banners/
|       |   |   |   |   `-- types.ts
|       |   |   |   |-- server/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   `-- invites.ts
|       |   |   |   |   `-- graphql/
|       |   |   |   |       `-- mutations.ts
|       |   |   |   |-- server-management/
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       |-- types.ts
|       |   |   |   |       `-- utils.ts
|       |   |   |   |-- settings/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- menu.ts
|       |   |   |   |   |   |-- state.ts
|       |   |   |   |   |   `-- workspaces.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       |-- constants.ts
|       |   |   |   |       |-- types.ts
|       |   |   |   |       `-- utils.ts
|       |   |   |   |-- tour/
|       |   |   |   |   |-- helpers.ts
|       |   |   |   |   `-- slideshowItems.ts
|       |   |   |   |-- user/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- activeWorkspace.ts
|       |   |   |   |   |   |-- avatar.ts
|       |   |   |   |   |   |-- emails.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- meta.ts
|       |   |   |   |   |   `-- projectUpdates.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   `-- queries.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       `-- components.ts
|       |   |   |   |-- viewer/
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   |-- filtering/
|       |   |   |   |   |   |   |-- coloringHelpers.ts
|       |   |   |   |   |   |   |-- counts.ts
|       |   |   |   |   |   |   |-- dataStore.ts
|       |   |   |   |   |   |   |-- filtering.ts
|       |   |   |   |   |   |   `-- setup.ts
|       |   |   |   |   |   |-- savedViews/
|       |   |   |   |   |   |   |-- general.ts
|       |   |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |   |-- state.ts
|       |   |   |   |   |   |   |-- subscriptions.ts
|       |   |   |   |   |   |   |-- ui.ts
|       |   |   |   |   |   |   `-- validation.ts
|       |   |   |   |   |   |-- setup/
|       |   |   |   |   |   |   |-- coloring.ts
|       |   |   |   |   |   |   |-- comments.ts
|       |   |   |   |   |   |   |-- core.ts
|       |   |   |   |   |   |   |-- dev.ts
|       |   |   |   |   |   |   |-- diff.ts
|       |   |   |   |   |   |   |-- embed.ts
|       |   |   |   |   |   |   |-- filters.ts
|       |   |   |   |   |   |   |-- highlighting.ts
|       |   |   |   |   |   |   |-- measurements.ts
|       |   |   |   |   |   |   |-- panels.ts
|       |   |   |   |   |   |   |-- postSetup.ts
|       |   |   |   |   |   |   |-- selection.ts
|       |   |   |   |   |   |   |-- urlHashState.ts
|       |   |   |   |   |   |   `-- viewMode.ts
|       |   |   |   |   |   |-- activity.ts
|       |   |   |   |   |   |-- anchorPoints.ts
|       |   |   |   |   |   |-- commentBubbles.ts
|       |   |   |   |   |   |-- commentManagement.ts
|       |   |   |   |   |   |-- contextMenu.ts
|       |   |   |   |   |   |-- resources.ts
|       |   |   |   |   |   |-- serialization.ts
|       |   |   |   |   |   |-- setup.ts
|       |   |   |   |   |   |-- tree.ts
|       |   |   |   |   |   |-- ui.ts
|       |   |   |   |   |   `-- viewer.ts
|       |   |   |   |   |-- extensions/
|       |   |   |   |   |   `-- PassReader.ts
|       |   |   |   |   |-- graphql/
|       |   |   |   |   |   |-- fragments.ts
|       |   |   |   |   |   |-- mutations.ts
|       |   |   |   |   |   |-- queries.ts
|       |   |   |   |   |   `-- subscriptions.ts
|       |   |   |   |   `-- helpers/
|       |   |   |   |       |-- filters/
|       |   |   |   |       |   |-- constants.ts
|       |   |   |   |       |   |-- types.ts
|       |   |   |   |       |   `-- utils.ts
|       |   |   |   |       |-- savedViews/
|       |   |   |   |       |   `-- cache.ts
|       |   |   |   |       |-- shortcuts/
|       |   |   |   |       |   |-- shortcuts.ts
|       |   |   |   |       |   `-- types.ts
|       |   |   |   |       |-- comments.ts
|       |   |   |   |       |-- emojis.ts
|       |   |   |   |       |-- eventBus.ts
|       |   |   |   |       |-- savedViews.ts
|       |   |   |   |       |-- sceneExplorer.ts
|       |   |   |   |       |-- state.ts
|       |   |   |   |       `-- three.ts
|       |   |   |   `-- workspaces/
|       |   |   |       |-- composables/
|       |   |   |       |   |-- projects/
|       |   |   |       |   |   `-- permissions.ts
|       |   |   |       |   |-- activeWorkspace.ts
|       |   |   |       |   |-- discoverableWorkspaces.ts
|       |   |   |       |   |-- joinRequests.ts
|       |   |   |       |   |-- limits.ts
|       |   |   |       |   |-- management.ts
|       |   |   |       |   |-- plan.ts
|       |   |   |       |   |-- projectUpdates.ts
|       |   |   |       |   |-- region.ts
|       |   |   |       |   |-- security.ts
|       |   |   |       |   |-- sso.ts
|       |   |   |       |   |-- usage.ts
|       |   |   |       |   `-- wizard.ts
|       |   |   |       |-- graphql/
|       |   |   |       |   |-- mutations.ts
|       |   |   |       |   |-- queries.ts
|       |   |   |       |   `-- subscriptions.ts
|       |   |   |       `-- helpers/
|       |   |   |           |-- middleware.ts
|       |   |   |           |-- roles.ts
|       |   |   |           `-- types.ts
|       |   |   |-- middleware/
|       |   |   |   |-- 001-fe2-header.global.ts
|       |   |   |   |-- 002-redirects.global.ts
|       |   |   |   |-- 003-acceptInvites.global.ts
|       |   |   |   |-- 004-onboarding.global.ts
|       |   |   |   |-- 999-parallelFinalize.ts
|       |   |   |   |-- admin.ts
|       |   |   |   |-- auth.ts
|       |   |   |   |-- canViewProjectTokens.ts
|       |   |   |   |-- canViewSettings.ts
|       |   |   |   |-- canViewWebhooks.ts
|       |   |   |   |-- dashboardRedirect.ts
|       |   |   |   |-- guest.ts
|       |   |   |   |-- headers.global.ts
|       |   |   |   |-- projectsActiveCheck.ts
|       |   |   |   |-- requireDiscoverableWorkspaces.ts
|       |   |   |   |-- requiresAutomateEnabled.ts
|       |   |   |   |-- requireSsoEnabled.ts
|       |   |   |   |-- requiresWorkspacesEnabled.ts
|       |   |   |   |-- requireValidAutomation.ts
|       |   |   |   |-- requireValidDashboard.ts
|       |   |   |   |-- requireValidFunction.ts
|       |   |   |   |-- requireValidModel.ts
|       |   |   |   |-- requireValidPresentation.ts
|       |   |   |   |-- requireValidProject.ts
|       |   |   |   |-- requireValidWorkspace.ts
|       |   |   |   |-- settings.ts
|       |   |   |   `-- thread.ts
|       |   |   |-- pages/
|       |   |   |   |-- authn/
|       |   |   |   |   |-- sso/
|       |   |   |   |   |   `-- index.vue
|       |   |   |   |   |-- verify/
|       |   |   |   |   |   `-- [appId]/
|       |   |   |   |   |       `-- [challenge]/
|       |   |   |   |   |           `-- index.vue
|       |   |   |   |   |-- forgotten-password.vue
|       |   |   |   |   |-- login.vue
|       |   |   |   |   |-- register.vue
|       |   |   |   |   `-- reset-password.vue
|       |   |   |   |-- connectors/
|       |   |   |   |   `-- index.vue
|       |   |   |   |-- files/
|       |   |   |   |   `-- index.vue
|       |   |   |   |-- functions/
|       |   |   |   |   `-- [fid].vue
|       |   |   |   |-- projects/
|       |   |   |   |   |-- [id]/
|       |   |   |   |   |   |-- add/
|       |   |   |   |   |   |   |-- model.vue
|       |   |   |   |   |   |   `-- pdf.vue
|       |   |   |   |   |   |-- index/
|       |   |   |   |   |   |   |-- automations/
|       |   |   |   |   |   |   |   |-- [aid].vue
|       |   |   |   |   |   |   |   `-- index.vue
|       |   |   |   |   |   |   |-- settings/
|       |   |   |   |   |   |   |   |-- index.vue
|       |   |   |   |   |   |   |   |-- integrations.vue
|       |   |   |   |   |   |   |   |-- tokens.vue
|       |   |   |   |   |   |   |   `-- webhooks.vue
|       |   |   |   |   |   |   |-- automations.vue
|       |   |   |   |   |   |   |-- collaborators.vue
|       |   |   |   |   |   |   |-- dashboards.vue
|       |   |   |   |   |   |   |-- discussions.vue
|       |   |   |   |   |   |   |-- index.vue
|       |   |   |   |   |   |   `-- settings.vue
|       |   |   |   |   |   |-- models/
|       |   |   |   |   |   |   `-- [modelId]/
|       |   |   |   |   |   |       |-- index.vue
|       |   |   |   |   |   |       `-- versions.vue
|       |   |   |   |   |   |-- presentations/
|       |   |   |   |   |   |   `-- [presentationId]/
|       |   |   |   |   |   |       `-- index.vue
|       |   |   |   |   |   |-- threads/
|       |   |   |   |   |   |   `-- [threadId].vue
|       |   |   |   |   |   `-- index.vue
|       |   |   |   |   `-- index.vue
|       |   |   |   |-- settings/
|       |   |   |   |   |-- server/
|       |   |   |   |   |   |-- general.vue
|       |   |   |   |   |   |-- members.vue
|       |   |   |   |   |   |-- projects.vue
|       |   |   |   |   |   `-- regions.vue
|       |   |   |   |   |-- user/
|       |   |   |   |   |   |-- developer.vue
|       |   |   |   |   |   |-- emails.vue
|       |   |   |   |   |   |-- notifications.vue
|       |   |   |   |   |   `-- profile.vue
|       |   |   |   |   |-- workspaces/
|       |   |   |   |   |   |-- [slug]/
|       |   |   |   |   |   |   |-- members/
|       |   |   |   |   |   |   |   |-- guests.vue
|       |   |   |   |   |   |   |   |-- index.vue
|       |   |   |   |   |   |   |   |-- invites.vue
|       |   |   |   |   |   |   |   `-- requests.vue
|       |   |   |   |   |   |   |-- automation.vue
|       |   |   |   |   |   |   |-- billing.vue
|       |   |   |   |   |   |   |-- general.vue
|       |   |   |   |   |   |   |-- integrations.vue
|       |   |   |   |   |   |   |-- members.vue
|       |   |   |   |   |   |   |-- projects.vue
|       |   |   |   |   |   |   |-- regions.vue
|       |   |   |   |   |   |   `-- security.vue
|       |   |   |   |   |   `-- [slug].vue
|       |   |   |   |   |-- server.vue
|       |   |   |   |   `-- user.vue
|       |   |   |   |-- tutorials/
|       |   |   |   |   `-- index.vue
|       |   |   |   |-- workspaces/
|       |   |   |   |   |-- [slug]/
|       |   |   |   |   |   |-- dashboards/
|       |   |   |   |   |   |   |-- [id].vue
|       |   |   |   |   |   |   `-- index.vue
|       |   |   |   |   |   |-- functions/
|       |   |   |   |   |   |   `-- index.vue
|       |   |   |   |   |   |-- sso/
|       |   |   |   |   |   |   |-- index.vue
|       |   |   |   |   |   |   |-- register.vue
|       |   |   |   |   |   |   `-- session-error.vue
|       |   |   |   |   |   `-- index.vue
|       |   |   |   |   `-- actions/
|       |   |   |   |       |-- create.vue
|       |   |   |   |       `-- join.vue
|       |   |   |   |-- authn.vue
|       |   |   |   |-- error-email-verify.vue
|       |   |   |   |-- error.vue
|       |   |   |   |-- index.vue
|       |   |   |   |-- onboarding.vue
|       |   |   |   `-- verify-email.vue
|       |   |   |-- plugins/
|       |   |   |   |-- 001-accessibility.ts
|       |   |   |   |-- 001-dayjs.ts
|       |   |   |   |-- 001-portal.ts
|       |   |   |   |-- 001-tippy.ts
|       |   |   |   |-- 010-hydration.ts
|       |   |   |   |-- 010-logger.ts
|       |   |   |   |-- 020-rum.ts
|       |   |   |   |-- 021-url.ts
|       |   |   |   |-- 030-healthMetrics.server.ts
|       |   |   |   |-- 040-redis.server.ts
|       |   |   |   |-- 050-cache.ts
|       |   |   |   |-- 060-dataPreload.ts
|       |   |   |   |-- 070-mpClient.client.ts
|       |   |   |   |-- 070-mpServer.server.ts
|       |   |   |   |-- 080-mp.client.ts
|       |   |   |   |-- dev.ts
|       |   |   |   |-- eventBus.ts
|       |   |   |   |-- intercom.client.ts
|       |   |   |   `-- preventLeaveOnUpload.client.ts
|       |   |   |-- public/
|       |   |   |   |-- images/
|       |   |   |   |   |-- functions/
|       |   |   |   |   |   |-- dotnet.svg
|       |   |   |   |   |   |-- python.svg
|       |   |   |   |   |   `-- typescript.svg
|       |   |   |   |   `-- workspace/
|       |   |   |   |       |-- explainer-video-dark.webp
|       |   |   |   |       `-- explainer-video-light.webp
|       |   |   |   |-- favicon.ico
|       |   |   |   |-- pdf.worker.min.mjs
|       |   |   |   `-- robots.txt
|       |   |   |-- server/
|       |   |   |   |-- api/
|       |   |   |   |   `-- status.ts
|       |   |   |   |-- lib/
|       |   |   |   |   `-- core/
|       |   |   |   |       `-- helpers/
|       |   |   |   |           |-- constants.ts
|       |   |   |   |           `-- observability.ts
|       |   |   |   |-- middleware/
|       |   |   |   |   |-- 001-logging.ts
|       |   |   |   |   |-- 002-setIdHeaderResponse.ts
|       |   |   |   |   |-- 003-cors.ts
|       |   |   |   |   `-- 004-sharedArrayBufferHeaders.ts
|       |   |   |   |-- plugins/
|       |   |   |   |   |-- 001-devLogsSync.ts
|       |   |   |   |   |-- 001-startupTermination.ts
|       |   |   |   |   `-- prevent404Cache.ts
|       |   |   |   |-- routes/
|       |   |   |   |   |-- web-api/
|       |   |   |   |   |   `-- cookie-fix.ts
|       |   |   |   |   `-- graphql.ts
|       |   |   |   |-- utils/
|       |   |   |   |   `-- logger.ts
|       |   |   |   `-- tsconfig.json
|       |   |   |-- tools/
|       |   |   |   `-- gqlCacheHelpersCodegenPlugin.js
|       |   |   |-- type-augmentations/
|       |   |   |   |-- eslint-only/
|       |   |   |   |   `-- vue-shim.d.ts
|       |   |   |   |-- stubs/
|       |   |   |   |   `-- types__react/
|       |   |   |   |       |-- index.d.ts
|       |   |   |   |       `-- package.json
|       |   |   |   |-- apollo.d.ts
|       |   |   |   |-- globals.d.ts
|       |   |   |   |-- marked-plaintext.d.ts
|       |   |   |   |-- mdx.d.ts
|       |   |   |   |-- nuxt.d.ts
|       |   |   |   |-- seq-logging.d.ts
|       |   |   |   |-- server.d.ts
|       |   |   |   |-- storybook.d.ts
|       |   |   |   |-- tweetnacl-sealedbox-js.d.ts
|       |   |   |   |-- vue.d.ts
|       |   |   |   `-- window.d.ts
|       |   |   |-- utils/
|       |   |   |   |-- globals.ts
|       |   |   |   `-- logging.ts
|       |   |   |-- .env.example
|       |   |   |-- .gitignore
|       |   |   |-- .stylelintignore
|       |   |   |-- app.vue
|       |   |   |-- codegen.ts
|       |   |   |-- Dockerfile
|       |   |   |-- error.vue
|       |   |   |-- eslint.config.mjs
|       |   |   |-- nuxt.config.ts
|       |   |   |-- package.json
|       |   |   |-- postcss.config.js
|       |   |   |-- readme.md
|       |   |   |-- stylelint.config.js
|       |   |   |-- tailwind.config.cjs
|       |   |   |-- tsconfig.eslint.json
|       |   |   `-- tsconfig.json
|       |   |-- ifc-import-service/
|       |   |   |-- src/
|       |   |   |   `-- ifc_importer/
|       |   |   |       |-- __init__.py
|       |   |   |       |-- client.py
|       |   |   |       |-- config.py
|       |   |   |       |-- domain.py
|       |   |   |       |-- job_manager.py
|       |   |   |       |-- process_job.py
|       |   |   |       `-- repository.py
|       |   |   |-- .env.example
|       |   |   |-- .gitignore
|       |   |   |-- .python-version
|       |   |   |-- Dockerfile
|       |   |   |-- job_processor.py
|       |   |   |-- main.py
|       |   |   |-- pyproject.toml
|       |   |   |-- README.md
|       |   |   |-- run.ps1
|       |   |   |-- run.sh
|       |   |   `-- uv.lock
|       |   |-- monitor-deployment/
|       |   |   |-- bin/
|       |   |   |   `-- www.js
|       |   |   |-- src/
|       |   |   |   |-- clients/
|       |   |   |   |   `-- knex.ts
|       |   |   |   |-- domain/
|       |   |   |   |   `-- const.ts
|       |   |   |   |-- observability/
|       |   |   |   |   |-- metrics/
|       |   |   |   |   |   |-- commits.ts
|       |   |   |   |   |   |-- dbMaxPerparedTransactions.ts
|       |   |   |   |   |   |-- dbPreparedTransactions.ts
|       |   |   |   |   |   |-- dbSize.ts
|       |   |   |   |   |   |-- fileImports.ts
|       |   |   |   |   |   |-- fileSize.ts
|       |   |   |   |   |   |-- maxConnections.ts
|       |   |   |   |   |   |-- objects.ts
|       |   |   |   |   |   |-- previews.ts
|       |   |   |   |   |   |-- streams.ts
|       |   |   |   |   |   |-- tableSize.ts
|       |   |   |   |   |   |-- users.ts
|       |   |   |   |   |   `-- webhooks.ts
|       |   |   |   |   |-- expressLogging.ts
|       |   |   |   |   |-- logging.ts
|       |   |   |   |   |-- metricsApp.ts
|       |   |   |   |   |-- metricsRoute.ts
|       |   |   |   |   |-- prometheusMetrics.ts
|       |   |   |   |   `-- types.ts
|       |   |   |   |-- server/
|       |   |   |   |   |-- routes/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   `-- server.ts
|       |   |   |   |-- utils/
|       |   |   |   |   |-- env.ts
|       |   |   |   |   `-- errorHandler.ts
|       |   |   |   |-- aliasLoader.ts
|       |   |   |   |-- bin.ts
|       |   |   |   |-- bootstrap.ts
|       |   |   |   `-- root.ts
|       |   |   |-- .env.example
|       |   |   |-- Dockerfile
|       |   |   |-- eslint.config.mjs
|       |   |   |-- multiregion.example.json
|       |   |   |-- package.json
|       |   |   |-- README.md
|       |   |   |-- tsconfig.build.json
|       |   |   |-- tsconfig.json
|       |   |   `-- vitest.config.ts
|       |   |-- objectloader/
|       |   |   |-- examples/
|       |   |   |   |-- browser/
|       |   |   |   |   |-- index.html
|       |   |   |   |   `-- script.js
|       |   |   |   `-- node/
|       |   |   |       `-- script.mjs
|       |   |   |-- src/
|       |   |   |   |-- errors/
|       |   |   |   |   `-- index.js
|       |   |   |   |-- helpers/
|       |   |   |   |   `-- stream.js
|       |   |   |   `-- index.js
|       |   |   |-- types/
|       |   |   |   |-- index.d.cts
|       |   |   |   `-- index.d.ts
|       |   |   |-- .babelrc
|       |   |   |-- .browserslistrc
|       |   |   |-- .gitignore
|       |   |   |-- eslint.config.mjs
|       |   |   |-- jsconfig.json
|       |   |   |-- package.json
|       |   |   |-- readme.md
|       |   |   `-- rollup.config.js
|       |   |-- objectloader2/
|       |   |   |-- src/
|       |   |   |   |-- core/
|       |   |   |   |   |-- __snapshots__/
|       |   |   |   |   |   |-- objectLoader2.spec.ts.snap
|       |   |   |   |   |   `-- traverser.spec.ts.snap
|       |   |   |   |   |-- stages/
|       |   |   |   |   |   |-- __snapshots__/
|       |   |   |   |   |   |   |-- cacheReader.spec.ts.snap
|       |   |   |   |   |   |   |-- indexedDatabase.spec.ts.snap
|       |   |   |   |   |   |   `-- serverDownloader.spec.ts.snap
|       |   |   |   |   |   |-- memory/
|       |   |   |   |   |   |   |-- __snapshots__/
|       |   |   |   |   |   |   |   `-- memoryDownloader.spec.ts.snap
|       |   |   |   |   |   |   |-- memoryDatabase.spec.ts
|       |   |   |   |   |   |   |-- memoryDatabase.ts
|       |   |   |   |   |   |   |-- memoryDownloader.spec.ts
|       |   |   |   |   |   |   `-- memoryDownloader.ts
|       |   |   |   |   |   |-- cacheReader.spec.ts
|       |   |   |   |   |   |-- cacheReader.ts
|       |   |   |   |   |   |-- cacheWriter.spec.ts
|       |   |   |   |   |   |-- cacheWriter.ts
|       |   |   |   |   |   |-- indexedDatabase.spec.ts
|       |   |   |   |   |   |-- indexedDatabase.ts
|       |   |   |   |   |   |-- serverDownloader.spec.ts
|       |   |   |   |   |   `-- serverDownloader.ts
|       |   |   |   |   |-- interfaces.ts
|       |   |   |   |   |-- objectLoader2.spec.ts
|       |   |   |   |   |-- objectLoader2.ts
|       |   |   |   |   |-- objectLoader2Factory.test.ts
|       |   |   |   |   |-- objectLoader2Factory.ts
|       |   |   |   |   |-- options.ts
|       |   |   |   |   |-- traverser.spec.ts
|       |   |   |   |   `-- traverser.ts
|       |   |   |   |-- deferment/
|       |   |   |   |   |-- defermentManager.test.ts
|       |   |   |   |   |-- defermentManager.ts
|       |   |   |   |   |-- deferredBase.ts
|       |   |   |   |   |-- MemoryCache.test.ts
|       |   |   |   |   `-- MemoryCache.ts
|       |   |   |   |-- queues/
|       |   |   |   |   |-- aggregateQueue.ts
|       |   |   |   |   |-- asyncGeneratorQueue.ts
|       |   |   |   |   |-- batchingQueue.dispose.test.ts
|       |   |   |   |   |-- batchingQueue.test.ts
|       |   |   |   |   |-- batchingQueue.ts
|       |   |   |   |   |-- bufferQueue.ts
|       |   |   |   |   |-- keyedQueue.test.ts
|       |   |   |   |   |-- keyedQueue.ts
|       |   |   |   |   `-- queue.ts
|       |   |   |   |-- test/
|       |   |   |   |   `-- e2e.spec.ts
|       |   |   |   |-- types/
|       |   |   |   |   |-- errors.ts
|       |   |   |   |   |-- functions.spec.ts
|       |   |   |   |   |-- functions.ts
|       |   |   |   |   `-- types.ts
|       |   |   |   `-- index.ts
|       |   |   |-- .gitignore
|       |   |   |-- .npmignore
|       |   |   |-- eslint.config.mjs
|       |   |   |-- package.json
|       |   |   |-- readme.md
|       |   |   |-- tsconfig.json
|       |   |   `-- vitest.config.ts
|       |   |-- objectsender/
|       |   |   |-- public/
|       |   |   |   `-- vite.svg
|       |   |   |-- src/
|       |   |   |   |-- examples/
|       |   |   |   |   `-- browser/
|       |   |   |   |       |-- main.ts
|       |   |   |   |       `-- utils.ts
|       |   |   |   |-- transports/
|       |   |   |   |   |-- ITransport.ts
|       |   |   |   |   `-- ServerTransport.ts
|       |   |   |   |-- utils/
|       |   |   |   |   |-- Base.ts
|       |   |   |   |   |-- Decorators.ts
|       |   |   |   |   |-- IDisposable.ts
|       |   |   |   |   `-- Serializer.ts
|       |   |   |   |-- index.ts
|       |   |   |   `-- vite-env.d.ts
|       |   |   |-- .gitignore
|       |   |   |-- .npmignore
|       |   |   |-- eslint.config.mjs
|       |   |   |-- index.html
|       |   |   |-- package.json
|       |   |   |-- readme.md
|       |   |   |-- tsconfig.eslint.json
|       |   |   |-- tsconfig.json
|       |   |   |-- vite.config.ts
|       |   |   `-- vitest.config.ts
|       |   |-- preview-frontend/
|       |   |   |-- src/
|       |   |   |   |-- main.ts
|       |   |   |   `-- vite-env.d.ts
|       |   |   |-- eslint.config.mjs
|       |   |   |-- index.html
|       |   |   |-- package.json
|       |   |   |-- README.md
|       |   |   `-- tsconfig.json
|       |   |-- preview-service/
|       |   |   |-- scripts/
|       |   |   |   `-- publishTask.ts
|       |   |   |-- src/
|       |   |   |   |-- bootstrap.ts
|       |   |   |   |-- config.ts
|       |   |   |   |-- jobProcessor.ts
|       |   |   |   |-- logging.ts
|       |   |   |   |-- main.ts
|       |   |   |   |-- metrics.ts
|       |   |   |   `-- server.ts
|       |   |   |-- tests/
|       |   |   |   `-- main.spec.ts
|       |   |   |-- .env.example
|       |   |   |-- .env.test-example
|       |   |   |-- .gitignore
|       |   |   |-- Dockerfile
|       |   |   |-- eslint.config.mjs
|       |   |   |-- package.json
|       |   |   |-- readme.md
|       |   |   |-- tsconfig.build.json
|       |   |   |-- tsconfig.json
|       |   |   `-- vitest.config.ts
|       |   |-- server/
|       |   |   |-- assets/
|       |   |   |   |-- acc/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       |-- acc.graphql
|       |   |   |   |       |-- integrations.graphql
|       |   |   |   |       |-- permissions.graphql
|       |   |   |   |       `-- syncItems.graphql
|       |   |   |   |-- accessrequests/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- accessrequests.graphql
|       |   |   |   |-- activitystream/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- activity.graphql
|       |   |   |   |-- apiexplorer/
|       |   |   |   |   `-- templates/
|       |   |   |   |       `-- explorer.html
|       |   |   |   |-- auth/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       |-- apps.graphql
|       |   |   |   |       `-- auth.graphql
|       |   |   |   |-- automate/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       |-- automate.graphql
|       |   |   |   |       `-- permissions.graphql
|       |   |   |   |-- blobstorage/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- blobstorage.graphql
|       |   |   |   |-- comments/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       |-- comments.gql
|       |   |   |   |       |-- permissions.graphql
|       |   |   |   |       `-- viewer.gql
|       |   |   |   |-- core/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       |-- admin.graphql
|       |   |   |   |       |-- apitoken.graphql
|       |   |   |   |       |-- branchesAndCommits.graphql
|       |   |   |   |       |-- common.graphql
|       |   |   |   |       |-- modelsAndVersions.graphql
|       |   |   |   |       |-- objects.graphql
|       |   |   |   |       |-- permissions.graphql
|       |   |   |   |       |-- projects.graphql
|       |   |   |   |       |-- server.graphql
|       |   |   |   |       |-- streams.graphql
|       |   |   |   |       |-- test.graphql
|       |   |   |   |       |-- user.graphql
|       |   |   |   |       |-- userEmails.graphql
|       |   |   |   |       `-- userMeta.graphql
|       |   |   |   |-- dashboards/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       |-- dashboards.graphql
|       |   |   |   |       |-- permissions.graphql
|       |   |   |   |       |-- shares.graphql
|       |   |   |   |       `-- tokens.graphql
|       |   |   |   |-- emails/
|       |   |   |   |   |-- config/
|       |   |   |   |   |   `-- .mjmlconfig
|       |   |   |   |   |-- templates/
|       |   |   |   |   |   |-- basic/
|       |   |   |   |   |   |   |-- basic.html
|       |   |   |   |   |   |   `-- basic.txt
|       |   |   |   |   |   |-- components/
|       |   |   |   |   |   |   |-- ctaButton.mjml
|       |   |   |   |   |   |   |-- digestTopic.ejs
|       |   |   |   |   |   |   |-- footer.mjml
|       |   |   |   |   |   |   |-- head.mjml
|       |   |   |   |   |   |   `-- headerLogo.mjml
|       |   |   |   |   |   |-- speckleBasicEmailTemplate.mjml.ejs
|       |   |   |   |   |   `-- speckleBasicEmailTemplate.txt.ejs
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- emails.graphql
|       |   |   |   |-- fileuploads/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- fileuploads.graphql
|       |   |   |   |-- gatekeeperCore/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       |-- gatekeeper.graphql
|       |   |   |   |       `-- workspaceSeats.graphql
|       |   |   |   |-- gendo/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- gendo.graphql
|       |   |   |   |-- multiregion/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- multiregion.graphql
|       |   |   |   |-- notifications/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- notificationPreferences.graphql
|       |   |   |   |-- serverinvites/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- serverInvites.graphql
|       |   |   |   |-- stats/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- stats.gql
|       |   |   |   |-- viewer/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       |-- permissions.graphql
|       |   |   |   |       |-- savedViews.graphql
|       |   |   |   |       |-- shares.graphql
|       |   |   |   |       `-- viewerResources.graphql
|       |   |   |   |-- webhooks/
|       |   |   |   |   `-- typedefs/
|       |   |   |   |       `-- webhooks.graphql
|       |   |   |   `-- workspacesCore/
|       |   |   |       `-- typedefs/
|       |   |   |           |-- permissions.graphql
|       |   |   |           |-- projects.graphql
|       |   |   |           |-- regions.graphql
|       |   |   |           |-- workspaceJoinRequests.graphql
|       |   |   |           `-- workspaces.graphql
|       |   |   |-- bin/
|       |   |   |   |-- gqlgen
|       |   |   |   |-- mocha
|       |   |   |   `-- www
|       |   |   |-- db/
|       |   |   |   |-- knex.ts
|       |   |   |   `-- migrations.ts
|       |   |   |-- healthchecks/
|       |   |   |   |-- tests/
|       |   |   |   |   |-- postgres.spec.ts
|       |   |   |   |   `-- redis.spec.ts
|       |   |   |   |-- connectionPool.ts
|       |   |   |   |-- errors.ts
|       |   |   |   |-- health.ts
|       |   |   |   |-- index.ts
|       |   |   |   |-- postgres.ts
|       |   |   |   |-- redis.ts
|       |   |   |   `-- types.ts
|       |   |   |-- modules/
|       |   |   |   |-- acc/
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   `-- autodesk/
|       |   |   |   |   |       |-- acc.ts
|       |   |   |   |   |       |-- helpers.ts
|       |   |   |   |   |       `-- tokens.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- acc/
|       |   |   |   |   |   |   |-- constants.ts
|       |   |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   `-- constants.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- acc.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   `-- eventListeners.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   |-- dataloaders/
|       |   |   |   |   |   |   `-- acc.ts
|       |   |   |   |   |   |-- mocks/
|       |   |   |   |   |   |   `-- mocks.ts
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       |-- acc.ts
|       |   |   |   |   |       |-- integrations.ts
|       |   |   |   |   |       `-- permissions.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- acc.ts
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   `-- svfUtils.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20250722122424_create_sync_items_table.ts
|       |   |   |   |   |   `-- 20250806163108_drop_automation_id_fk.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- accSyncItems.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   |-- oidc.ts
|       |   |   |   |   |   `-- webhooks.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- automate.ts
|       |   |   |   |   |   |-- cron.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   `-- webhooks.ts
|       |   |   |   |   |-- dbSchema.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- accessrequests/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   `-- operations.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- graphTypes.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   `-- 20220829102231_add_server_access_requests_table.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- eventListener.ts
|       |   |   |   |   |   `-- stream.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- projectAccessRequests.spec.ts
|       |   |   |   |   |   `-- streamAccessRequests.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- activitystream/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- activityStream.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   |-- accessRequestListeners.ts
|       |   |   |   |   |   |-- branchListeners.ts
|       |   |   |   |   |   |-- commentListeners.ts
|       |   |   |   |   |   |-- commitListeners.ts
|       |   |   |   |   |   |-- gatekeeperListeners.ts
|       |   |   |   |   |   |-- streamInviteListeners.ts
|       |   |   |   |   |   |-- streamListeners.ts
|       |   |   |   |   |   |-- userListeners.ts
|       |   |   |   |   |   `-- workspaceListeners.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- activity.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20210616173000_stream_activity.js
|       |   |   |   |   |   |-- 20250613121055_add_index_on_actionType_to_stream_activity.ts
|       |   |   |   |   |   `-- 20250625095012_activity.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- backfillActivity.ts
|       |   |   |   |   |   `-- summary.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   `-- integration/
|       |   |   |   |   |       |-- repository/
|       |   |   |   |   |       |   |-- activity.spec.ts
|       |   |   |   |   |       |   `-- activityStream.spec.ts
|       |   |   |   |   |       |-- activity.graph.spec.ts
|       |   |   |   |   |       |-- activitySummary.spec.ts
|       |   |   |   |   |       `-- backfillActivity.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- apiexplorer/
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- auth/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- const.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       |-- apps.ts
|       |   |   |   |   |       `-- auth.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   |-- oidc.spec.ts
|       |   |   |   |   |   |-- oidc.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   `-- 2020-05-29-apps.js
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- apps.ts
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- mailchimp.ts
|       |   |   |   |   |   |-- passportService.ts
|       |   |   |   |   |   `-- serverApps.ts
|       |   |   |   |   |-- strategies/
|       |   |   |   |   |   |-- azureAd.ts
|       |   |   |   |   |   |-- github.ts
|       |   |   |   |   |   |-- google.ts
|       |   |   |   |   |   |-- local.ts
|       |   |   |   |   |   `-- oidc.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   `-- registration.ts
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   `-- registration.spec.ts
|       |   |   |   |   |   |-- apps.graphql.spec.ts
|       |   |   |   |   |   |-- apps.spec.ts
|       |   |   |   |   |   `-- auth.spec.ts
|       |   |   |   |   |-- defaultApps.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   |-- middleware.ts
|       |   |   |   |   |-- scopes.ts
|       |   |   |   |   `-- strategies.ts
|       |   |   |   |-- automate/
|       |   |   |   |   |-- authz/
|       |   |   |   |   |   `-- loaders/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   `-- executionEngine.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |-- logic.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   |-- core.ts
|       |   |   |   |   |   |-- executionEngine.ts
|       |   |   |   |   |   |-- functions.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   `-- runs.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   |-- mocks/
|       |   |   |   |   |   |   `-- automate.ts
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       |-- automate.ts
|       |   |   |   |   |       `-- permissions.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- executionEngine.ts
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20230905162038_automations.ts
|       |   |   |   |   |   |-- 20230912114629_automations_tables_normalization.ts
|       |   |   |   |   |   |-- 20230914071540_make_function_run_results_nullable.ts
|       |   |   |   |   |   |-- 20230920130032_fix_project_delete_cascade.ts
|       |   |   |   |   |   |-- 20231025100054_automation_function_name_and_logo.ts
|       |   |   |   |   |   |-- 20240304143445_rename_tables.ts
|       |   |   |   |   |   |-- 20240305120620_automate.ts
|       |   |   |   |   |   |-- 20240321092858_triggers.ts
|       |   |   |   |   |   |-- 20240404075414_revision_active.ts
|       |   |   |   |   |   |-- 20240404173455_automation_token.ts
|       |   |   |   |   |   |-- 20240507075055_add_function_run_timestamps.ts
|       |   |   |   |   |   |-- 20240507140149_add_encryption_support.ts
|       |   |   |   |   |   |-- 20240523192300_add_is_test_automation_column.ts
|       |   |   |   |   |   |-- 20240620105859_drop_beta_tables.ts
|       |   |   |   |   |   |-- 20241203212110_cascade_delete_automations.ts
|       |   |   |   |   |   `-- 20250422161129_soft_delete_automations.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- automations.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   |-- authGithubApp.ts
|       |   |   |   |   |   `-- logStream.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- authCode.ts
|       |   |   |   |   |   |-- automationManagement.ts
|       |   |   |   |   |   |-- encryption.ts
|       |   |   |   |   |   |-- functionManagement.ts
|       |   |   |   |   |   |-- runsManagement.ts
|       |   |   |   |   |   |-- tracking.ts
|       |   |   |   |   |   `-- trigger.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- automations.spec.ts
|       |   |   |   |   |   `-- trigger.spec.ts
|       |   |   |   |   |-- utils/
|       |   |   |   |   |   |-- automateFunctionRunStatus.ts
|       |   |   |   |   |   |-- automationConfigurationValidator.ts
|       |   |   |   |   |   |-- inputSchemaValidator.ts
|       |   |   |   |   |   `-- jsonSchemaRedactor.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- backgroundjobs/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20250624121042_fileimport_job_queue.ts
|       |   |   |   |   |   `-- 20250904122458_compute_budget.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- backgroundjobs.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   `-- create.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   `-- repositories.spec.ts
|       |   |   |   |   |   `-- unit/
|       |   |   |   |   |       `-- services.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- blobstorage/
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   |-- objectStorage.ts
|       |   |   |   |   |   `-- supabaseStorage.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |-- storageOperations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- blobs.ts
|       |   |   |   |   |   |-- db.ts
|       |   |   |   |   |   |-- storageProvider.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 202206030936_add_asset_storage.js
|       |   |   |   |   |   |-- 202206231429_add_file_hash_to_blobs.js
|       |   |   |   |   |   `-- 20220727091536_blobs-id-length-removal.js
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- blobs.ts
|       |   |   |   |   |   |-- index.ts
|       |   |   |   |   |   `-- supabaseBlobs.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   |-- busboy.ts
|       |   |   |   |   |   `-- router.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- presigned.ts
|       |   |   |   |   |   `-- streams.ts
|       |   |   |   |   |-- tasks/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- e2e/
|       |   |   |   |   |   |   |-- blobstorage.graph.spec.ts
|       |   |   |   |   |   |   `-- blobstorage.rest.spec.ts
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   |-- blobstorage.integration.spec.ts
|       |   |   |   |   |   |   `-- presigned.integration.spec.ts
|       |   |   |   |   |   |-- unit/
|       |   |   |   |   |   |   `-- presigned.spec.ts
|       |   |   |   |   |   `-- helpers.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- cli/
|       |   |   |   |   |-- commands/
|       |   |   |   |   |   |-- activities/
|       |   |   |   |   |   |   `-- send.ts
|       |   |   |   |   |   |-- bull/
|       |   |   |   |   |   |   |-- monitor.ts
|       |   |   |   |   |   |   |-- test-consume.ts
|       |   |   |   |   |   |   `-- test-push.ts
|       |   |   |   |   |   |-- db/
|       |   |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   |   `-- index.ts
|       |   |   |   |   |   |   |-- migrate/
|       |   |   |   |   |   |   |   |-- create.ts
|       |   |   |   |   |   |   |   |-- down.ts
|       |   |   |   |   |   |   |   |-- latest.ts
|       |   |   |   |   |   |   |   |-- rollback.ts
|       |   |   |   |   |   |   |   `-- up.ts
|       |   |   |   |   |   |   |-- seed/
|       |   |   |   |   |   |   |   |-- commits.ts
|       |   |   |   |   |   |   |   `-- users.ts
|       |   |   |   |   |   |   |-- migrate.ts
|       |   |   |   |   |   |   |-- purge-test-dbs.ts
|       |   |   |   |   |   |   `-- seed.ts
|       |   |   |   |   |   |-- download/
|       |   |   |   |   |   |   |-- commit.ts
|       |   |   |   |   |   |   `-- project.ts
|       |   |   |   |   |   |-- graphql/
|       |   |   |   |   |   |   `-- introspect.ts
|       |   |   |   |   |   |-- stream/
|       |   |   |   |   |   |   `-- clone.ts
|       |   |   |   |   |   |-- test/
|       |   |   |   |   |   |   |-- generate-key-pair.ts
|       |   |   |   |   |   |   `-- test-meta.ts
|       |   |   |   |   |   |-- workspaces/
|       |   |   |   |   |   |   `-- set-plan.ts
|       |   |   |   |   |   |-- activities.ts
|       |   |   |   |   |   |-- bull.ts
|       |   |   |   |   |   |-- db.ts
|       |   |   |   |   |   |-- download.ts
|       |   |   |   |   |   |-- graphql.ts
|       |   |   |   |   |   |-- stream.ts
|       |   |   |   |   |   |-- test.ts
|       |   |   |   |   |   `-- workspaces.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   `-- readme.md
|       |   |   |   |-- comments/
|       |   |   |   |   |-- authz/
|       |   |   |   |   |   `-- loaders/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   `-- subscriptionListeners.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   |-- dataloaders/
|       |   |   |   |   |   |   `-- index.ts
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       |-- comments.ts
|       |   |   |   |   |       `-- permissions.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20220222173000_comments.js
|       |   |   |   |   |   `-- 20220722110643_fix_comments_delete_cascade.js
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- comments.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- commentTextService.ts
|       |   |   |   |   |   |-- data.ts
|       |   |   |   |   |   |-- index.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- notifications.ts
|       |   |   |   |   |   `-- retrieval.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- comments.graph.spec.ts
|       |   |   |   |   |   |-- comments.spec.ts
|       |   |   |   |   |   `-- projectComments.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- core/
|       |   |   |   |   |-- authz/
|       |   |   |   |   |   `-- loaders/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- configs/
|       |   |   |   |   |   |-- cors.ts
|       |   |   |   |   |   `-- knexMigrations.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- branches/
|       |   |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- commits/
|       |   |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- objects/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- projects/
|       |   |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |   |-- logic.ts
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- scheduledTasks/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- server/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- streams/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- tokens/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- userEmails/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   `-- users/
|       |   |   |   |   |       |-- events.ts
|       |   |   |   |   |       |-- operations.ts
|       |   |   |   |   |       `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   |-- automate.ts
|       |   |   |   |   |   |-- branch.ts
|       |   |   |   |   |   |-- commit.ts
|       |   |   |   |   |   |-- model.ts
|       |   |   |   |   |   |-- object.ts
|       |   |   |   |   |   |-- projects.ts
|       |   |   |   |   |   |-- ratelimit.ts
|       |   |   |   |   |   |-- stream.ts
|       |   |   |   |   |   |-- tokens.ts
|       |   |   |   |   |   |-- user.ts
|       |   |   |   |   |   |-- userEmails.ts
|       |   |   |   |   |   |-- userinput.ts
|       |   |   |   |   |   `-- workspaces.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   |-- projectListeners.ts
|       |   |   |   |   |   |-- subscriptionListeners.ts
|       |   |   |   |   |   `-- userTracking.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   |-- dataloaders/
|       |   |   |   |   |   |   `-- index.ts
|       |   |   |   |   |   |-- directives/
|       |   |   |   |   |   |   |-- hasRole.ts
|       |   |   |   |   |   |   |-- hasScope.ts
|       |   |   |   |   |   |   `-- isOwner.ts
|       |   |   |   |   |   |-- generated/
|       |   |   |   |   |   |   `-- graphql.ts
|       |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   `-- directiveHelper.ts
|       |   |   |   |   |   |-- mocks/
|       |   |   |   |   |   |   `-- core.ts
|       |   |   |   |   |   |-- plugins/
|       |   |   |   |   |   |   |-- logging.ts
|       |   |   |   |   |   |   `-- statusCode.ts
|       |   |   |   |   |   |-- resolvers/
|       |   |   |   |   |   |   |-- admin.ts
|       |   |   |   |   |   |   |-- apitoken.ts
|       |   |   |   |   |   |   |-- appTokens.ts
|       |   |   |   |   |   |   |-- base.ts
|       |   |   |   |   |   |   |-- branches.ts
|       |   |   |   |   |   |   |-- commits.ts
|       |   |   |   |   |   |   |-- common.ts
|       |   |   |   |   |   |   |-- embedTokens.ts
|       |   |   |   |   |   |   |-- models.ts
|       |   |   |   |   |   |   |-- objects.ts
|       |   |   |   |   |   |   |-- permissions.ts
|       |   |   |   |   |   |   |-- projects.ts
|       |   |   |   |   |   |   |-- server.ts
|       |   |   |   |   |   |   |-- streams.ts
|       |   |   |   |   |   |   |-- userEmails.ts
|       |   |   |   |   |   |   |-- users.ts
|       |   |   |   |   |   |   `-- versions.ts
|       |   |   |   |   |   |-- schema/
|       |   |   |   |   |   |   `-- baseTypeDefs.ts
|       |   |   |   |   |   |-- scalars.ts
|       |   |   |   |   |   |-- schema.ts
|       |   |   |   |   |   `-- setup.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- branch.ts
|       |   |   |   |   |   |-- features.ts
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   |-- mainConstants.ts
|       |   |   |   |   |   |-- meta.ts
|       |   |   |   |   |   |-- project.ts
|       |   |   |   |   |   |-- routeHelper.ts
|       |   |   |   |   |   |-- scanTable.ts
|       |   |   |   |   |   |-- server.ts
|       |   |   |   |   |   |-- testHelpers.ts
|       |   |   |   |   |   |-- token.ts
|       |   |   |   |   |   |-- types.ts
|       |   |   |   |   |   `-- userHelper.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 000-core.js
|       |   |   |   |   |   |-- 20201222100048_add_sourceapp_to_commits.js
|       |   |   |   |   |   |-- 20201222101522_add_totalchildrencount_to_commits.js
|       |   |   |   |   |   |-- 20201223120532_add_commit_parents_simplification.js
|       |   |   |   |   |   |-- 20201230111428_add_scopes_public_field.js
|       |   |   |   |   |   |-- 20210225130308_add_roles_public_field.js
|       |   |   |   |   |   |-- 20210314101154_add_invitefield_to_serverinfo.js
|       |   |   |   |   |   |-- 20210322190000_add_streamid_to_objects.js
|       |   |   |   |   |   |-- 20210603160000_optional_user_references.js
|       |   |   |   |   |   |-- 20211119105730_de_duplicate_users.js
|       |   |   |   |   |   |-- 20220315140000_ratelimit.js
|       |   |   |   |   |   |-- 20220318121405_add_stream_favorites.js
|       |   |   |   |   |   |-- 20220412150558_stream-public-comments.js
|       |   |   |   |   |   |-- 20220707135553_make_users_email_not_nullable.js
|       |   |   |   |   |   |-- 20220803104832_ts_test.ts
|       |   |   |   |   |   |-- 20220819091523_add_stream_discoverable_field.ts
|       |   |   |   |   |   |-- 20220823100915_migrate_streams_to_lower_precision_timestamps.ts
|       |   |   |   |   |   |-- 20220921084935_fix_branch_nullability.ts
|       |   |   |   |   |   |-- 20220929141717_scheduled_tasks.ts
|       |   |   |   |   |   |-- 20221122133014_add_user_onboarding_data.ts
|       |   |   |   |   |   |-- 20221213124322_migrate_more_table_precisions.ts
|       |   |   |   |   |   |-- 20230316091225_create_users_meta_table.ts
|       |   |   |   |   |   |-- 20230316132827_remove_user_is_onboarding_complete_col.ts
|       |   |   |   |   |   |-- 20230330082209_stricter_file_uploads_schema.ts
|       |   |   |   |   |   |-- 20230713094611_create_streams_meta_table.ts
|       |   |   |   |   |   |-- 20230727150957_serverGuestMode.ts
|       |   |   |   |   |   |-- 20240109101048_create_token_resource_access_table.ts
|       |   |   |   |   |   |-- 20240703084247_user-emails.ts
|       |   |   |   |   |   |-- 20240710154658_user_emails_backfill.ts
|       |   |   |   |   |   |-- 20241101055531_project_region.ts
|       |   |   |   |   |   |-- 20241102055157_project_region_nofk.ts
|       |   |   |   |   |   |-- 20250127172429_drop_closures.ts
|       |   |   |   |   |   |-- 20250506114120_add_streams_visibility_col.ts
|       |   |   |   |   |   |-- 20250514125149_remove_streams_ispublic_isdiscoverable.ts
|       |   |   |   |   |   |-- 20250630073647_add_embed_tokens.ts
|       |   |   |   |   |   |-- 20250701164407_object_preview_attempts.ts
|       |   |   |   |   |   |-- 20250722150843_lowercaseify_all_user_emails.ts
|       |   |   |   |   |   |-- 20250820101112_drop_user_defaults.ts
|       |   |   |   |   |   |-- 20250826074024_drop_stream_defaults.ts
|       |   |   |   |   |   `-- readme.md
|       |   |   |   |   |-- patches/
|       |   |   |   |   |   `-- knex.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- branches.ts
|       |   |   |   |   |   |-- commits.ts
|       |   |   |   |   |   |-- embedTokens.ts
|       |   |   |   |   |   |-- models.ts
|       |   |   |   |   |   |-- objects.ts
|       |   |   |   |   |   |-- projects.ts
|       |   |   |   |   |   |-- scheduledTasks.ts
|       |   |   |   |   |   |-- server.ts
|       |   |   |   |   |   |-- streams.ts
|       |   |   |   |   |   |-- tokens.ts
|       |   |   |   |   |   |-- userEmails.ts
|       |   |   |   |   |   |-- users.ts
|       |   |   |   |   |   `-- versions.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   |-- defaultErrorHandler.ts
|       |   |   |   |   |   |-- diffDownload.ts
|       |   |   |   |   |   |-- diffUpload.ts
|       |   |   |   |   |   |-- download.ts
|       |   |   |   |   |   |-- monitoring.ts
|       |   |   |   |   |   |-- ratelimiter.ts
|       |   |   |   |   |   |-- speckleObjectsStream.ts
|       |   |   |   |   |   |-- static.ts
|       |   |   |   |   |   `-- upload.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- branch/
|       |   |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |   `-- retrieval.ts
|       |   |   |   |   |   |-- commit/
|       |   |   |   |   |   |   |-- batchCommitActions.ts
|       |   |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |   |-- retrieval.ts
|       |   |   |   |   |   |   `-- viewerResources.ts
|       |   |   |   |   |   |-- objects/
|       |   |   |   |   |   |   `-- management.ts
|       |   |   |   |   |   |-- server/
|       |   |   |   |   |   |   `-- tracking.ts
|       |   |   |   |   |   |-- streams/
|       |   |   |   |   |   |   |-- access.ts
|       |   |   |   |   |   |   |-- auth.ts
|       |   |   |   |   |   |   |-- clone.ts
|       |   |   |   |   |   |   |-- discoverableStreams.ts
|       |   |   |   |   |   |   |-- favorite.ts
|       |   |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |   `-- onboarding.ts
|       |   |   |   |   |   |-- users/
|       |   |   |   |   |   |   |-- emailVerification.ts
|       |   |   |   |   |   |   |-- legacyAdminUsersList.ts
|       |   |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |   `-- tracking.ts
|       |   |   |   |   |   |-- admin.ts
|       |   |   |   |   |   |-- projects.ts
|       |   |   |   |   |   |-- richTextEditorService.ts
|       |   |   |   |   |   |-- taskScheduler.ts
|       |   |   |   |   |   |-- tokens.ts
|       |   |   |   |   |   `-- userEmails.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   |-- graphql/
|       |   |   |   |   |   |   |   `-- limits.ts
|       |   |   |   |   |   |   |-- creation.ts
|       |   |   |   |   |   |   `-- graphql.ts
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   |-- repositories/
|       |   |   |   |   |   |   |   |-- project.spec.ts
|       |   |   |   |   |   |   |   |-- users.spec.ts
|       |   |   |   |   |   |   |   `-- versions.spec.ts
|       |   |   |   |   |   |   |-- admin.graph.spec.ts
|       |   |   |   |   |   |   |-- admin.spec.ts
|       |   |   |   |   |   |   |-- commits.graph.spec.ts
|       |   |   |   |   |   |   |-- createUser.spec.ts
|       |   |   |   |   |   |   |-- emailVerification.spec.ts
|       |   |   |   |   |   |   |-- findUsers.spec.ts
|       |   |   |   |   |   |   |-- limits.graph.spec.ts
|       |   |   |   |   |   |   |-- objects.graph.spec.ts
|       |   |   |   |   |   |   |-- objects.rest.spec.ts
|       |   |   |   |   |   |   |-- objects.spec.ts
|       |   |   |   |   |   |   |-- objectsStream.rest.spec.ts
|       |   |   |   |   |   |   |-- projectRepositories.spec.ts
|       |   |   |   |   |   |   |-- projects.graph.spec.ts
|       |   |   |   |   |   |   |-- scanTable.spec.ts
|       |   |   |   |   |   |   |-- scheduledTasks.spec.ts
|       |   |   |   |   |   |   |-- subs.graph.spec.ts
|       |   |   |   |   |   |   |-- updateUser.spec.ts
|       |   |   |   |   |   |   |-- userEmails.graph.spec.ts
|       |   |   |   |   |   |   |-- userEmails.spec.ts
|       |   |   |   |   |   |   |-- userMeta.graph.spec.ts
|       |   |   |   |   |   |   |-- users.graph.spec.ts
|       |   |   |   |   |   |   `-- versions.graph.spec.ts
|       |   |   |   |   |   |-- unit/
|       |   |   |   |   |   |   |-- projects.spec.ts
|       |   |   |   |   |   |   `-- scheduledTasks.spec.ts
|       |   |   |   |   |   |-- apitokens.spec.ts
|       |   |   |   |   |   |-- batchCommits.spec.ts
|       |   |   |   |   |   |-- branches.spec.ts
|       |   |   |   |   |   |-- chunking.spec.ts
|       |   |   |   |   |   |-- commits.spec.ts
|       |   |   |   |   |   |-- commitsGraphql.spec.ts
|       |   |   |   |   |   |-- embedTokens.spec.ts
|       |   |   |   |   |   |-- favoriteStreams.spec.ts
|       |   |   |   |   |   |-- generic.spec.ts
|       |   |   |   |   |   |-- graph.spec.ts
|       |   |   |   |   |   |-- health.spec.ts
|       |   |   |   |   |   |-- init.spec.ts
|       |   |   |   |   |   |-- models.spec.ts
|       |   |   |   |   |   |-- objects.spec.ts
|       |   |   |   |   |   |-- projects.spec.ts
|       |   |   |   |   |   |-- ratelimiter.spec.ts
|       |   |   |   |   |   |-- rest.spec.ts
|       |   |   |   |   |   |-- streams.spec.ts
|       |   |   |   |   |   |-- users.spec.ts
|       |   |   |   |   |   |-- usersAdmin.spec.ts
|       |   |   |   |   |   |-- usersAdminList.spec.ts
|       |   |   |   |   |   |-- usersGraphql.spec.ts
|       |   |   |   |   |   `-- versions.spec.ts
|       |   |   |   |   |-- utils/
|       |   |   |   |   |   |-- chunking.ts
|       |   |   |   |   |   |-- dbNotificationListener.ts
|       |   |   |   |   |   |-- formatting.ts
|       |   |   |   |   |   `-- ratelimiter.ts
|       |   |   |   |   |-- dbSchema.ts
|       |   |   |   |   |-- hooks.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   |-- loaders.ts
|       |   |   |   |   |-- logger.ts
|       |   |   |   |   |-- roles.ts
|       |   |   |   |   `-- scopes.ts
|       |   |   |   |-- cross-server-sync/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   `-- operations.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- commit.ts
|       |   |   |   |   |   |-- onboardingProject.ts
|       |   |   |   |   |   `-- project.ts
|       |   |   |   |   |-- utils/
|       |   |   |   |   |   `-- graphqlClient.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- dashboards/
|       |   |   |   |   |-- authz/
|       |   |   |   |   |   `-- loaders/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- tokens/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- dashboards.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       |-- dashboards.ts
|       |   |   |   |   |       |-- permissions.ts
|       |   |   |   |   |       |-- shares.ts
|       |   |   |   |   |       `-- tokens.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- graphTypes.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20250826113850_dashboards.ts
|       |   |   |   |   |   |-- 20250826161638_dashboard_tokens.ts
|       |   |   |   |   |   `-- 20250916111351_dashboard_shares.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   `-- tokens.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- shares.ts
|       |   |   |   |   |   `-- tokens.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   `-- management.spec.ts
|       |   |   |   |   |   `-- unit/
|       |   |   |   |   |       |-- management.spec.ts
|       |   |   |   |   |       `-- tokens.spec.ts
|       |   |   |   |   |-- dbSchema.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- emails/
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   |-- jsonEcho.ts
|       |   |   |   |   |   |-- smtp.ts
|       |   |   |   |   |   `-- transportBuilder.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- consts.ts
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20220118181256-email-verifications.js
|       |   |   |   |   |   |-- 20220825082631_drop_email_verifications_used_col.ts
|       |   |   |   |   |   |-- 20250120145453_add_code_column_to_email_verifications.ts
|       |   |   |   |   |   `-- 20250123133749_remove_unique_email_verifications.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- verification/
|       |   |   |   |   |   |   |-- finalize.ts
|       |   |   |   |   |   |   `-- request.ts
|       |   |   |   |   |   |-- emailRendering.ts
|       |   |   |   |   |   `-- sending.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- emailTemplating.spec.ts
|       |   |   |   |   |   `-- verifications.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- fileuploads/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- consts.ts
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   |-- eventListener.ts
|       |   |   |   |   |   `-- subscriptionListeners.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- fileUploads.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- convert.ts
|       |   |   |   |   |   |-- errors.ts
|       |   |   |   |   |   |-- rest.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20210915130000-fileuploads.js
|       |   |   |   |   |   |-- 20250508190226_add_modelId_to_file_uploads.ts
|       |   |   |   |   |   |-- 20250514131509_add_modelId_foreign_to_file_uploads.ts
|       |   |   |   |   |   |-- 20250519074720_fileimport_message_text.ts
|       |   |   |   |   |   |-- 20250613070024_add_metadata_to_file_uploads.ts
|       |   |   |   |   |   |-- 20250616114012_drop_metadata_in_file_uploads.ts
|       |   |   |   |   |   `-- 20250716154353_add_performanceData_to_file_uploads.ts
|       |   |   |   |   |-- observability/
|       |   |   |   |   |   `-- metrics.ts
|       |   |   |   |   |-- queues/
|       |   |   |   |   |   `-- fileimports.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- fileUploads.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- router.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- createFileImport.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- presigned.ts
|       |   |   |   |   |   |-- resultHandler.ts
|       |   |   |   |   |   |-- resultListener.ts
|       |   |   |   |   |   `-- tasks.ts
|       |   |   |   |   |-- tasks/
|       |   |   |   |   |   |-- expireFileImports.ts
|       |   |   |   |   |   `-- garbageCollectBackgroundJobs.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- e2e/
|       |   |   |   |   |   |   `-- presigned.graph.spec.ts
|       |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   |-- creation.ts
|       |   |   |   |   |   |   `-- init.ts
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   |-- fileuploads.spec.ts
|       |   |   |   |   |   |   |-- presigned.integration.spec.ts
|       |   |   |   |   |   |   |-- results.graphql.spec.ts
|       |   |   |   |   |   |   `-- tasks.spec.ts
|       |   |   |   |   |   `-- unit/
|       |   |   |   |   |       |-- eventListener.spec.ts
|       |   |   |   |   |       |-- fileuploads.spec.ts
|       |   |   |   |   |       `-- presigned.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- gatekeeper/
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   |-- checkout/
|       |   |   |   |   |   |   `-- createCheckoutSession.ts
|       |   |   |   |   |   |-- getResultUrl.ts
|       |   |   |   |   |   `-- stripe.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- billing.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   |-- billing.ts
|       |   |   |   |   |   |-- features.ts
|       |   |   |   |   |   `-- license.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   `-- eventListener.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   |-- dataloaders/
|       |   |   |   |   |   |   `-- index.ts
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   |-- plans.ts
|       |   |   |   |   |   `-- prices.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- billing.ts
|       |   |   |   |   |   `-- workspaceSeat.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- billing.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- checkout/
|       |   |   |   |   |   |   `-- startCheckoutSession.ts
|       |   |   |   |   |   |-- subscriptions/
|       |   |   |   |   |   |   |-- calculateNewBillingCycleEnd.ts
|       |   |   |   |   |   |   |-- manageSubscriptionDownscale.ts
|       |   |   |   |   |   |   |-- mutateSubscriptionDataWithNewValidSeatNumbers.ts
|       |   |   |   |   |   |   `-- upgradeWorkspaceSubscription.ts
|       |   |   |   |   |   |-- checkout.ts
|       |   |   |   |   |   |-- featureAuthorization.ts
|       |   |   |   |   |   |-- prices.spec.ts
|       |   |   |   |   |   |-- prices.ts
|       |   |   |   |   |   |-- readOnly.ts
|       |   |   |   |   |   |-- subscriptions.ts
|       |   |   |   |   |   |-- upgrades.ts
|       |   |   |   |   |   |-- validateLicense.ts
|       |   |   |   |   |   `-- workspacePlans.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   |-- stripe.ts
|       |   |   |   |   |   |   `-- workspacePlan.ts
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   |-- repositories/
|       |   |   |   |   |   |   |   `-- workspacePlan.spec.ts
|       |   |   |   |   |   |   |-- billingRepositories.spec.ts
|       |   |   |   |   |   |   |-- prices.spec.ts
|       |   |   |   |   |   |   `-- workspace.graph.spec.ts
|       |   |   |   |   |   |-- unit/
|       |   |   |   |   |   |   |-- checkout.spec.ts
|       |   |   |   |   |   |   |-- featureAuthorization.spec.ts
|       |   |   |   |   |   |   |-- readOnly.spec.ts
|       |   |   |   |   |   |   |-- stripe.spec.ts
|       |   |   |   |   |   |   |-- subscriptions.spec.ts
|       |   |   |   |   |   |   |-- validateLicense.spec.ts
|       |   |   |   |   |   |   `-- workspacePlans.spec.ts
|       |   |   |   |   |   `-- helpers.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   |-- LICENSE
|       |   |   |   |   `-- scopes.ts
|       |   |   |   |-- gatekeeperCore/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- billing.ts
|       |   |   |   |   |   `-- events.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- graphTypes.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20241018132400_workspace_checkout.ts
|       |   |   |   |   |   |-- 20241105144301_cascade_delete_workspace_plans.ts
|       |   |   |   |   |   |-- 20241120063859_cascade_delete_checkout_session.ts
|       |   |   |   |   |   |-- 20241126084242_workspace_plan_rename.ts
|       |   |   |   |   |   |-- 20241126142602_workspace_plan_date.ts
|       |   |   |   |   |   |-- 20250224141824_create_workspace_seats_table.ts
|       |   |   |   |   |   |-- 20250410144546_subscription_currencies.ts
|       |   |   |   |   |   |-- 20250424064652_migrate_old_plans.ts
|       |   |   |   |   |   |-- 20250521102621_add_updatedAt_to_workspace_plans.ts
|       |   |   |   |   |   |-- 20250528074132_add_default_seat_type.ts
|       |   |   |   |   |   |-- 20250620072434_add_userId_to_workspaceCheckoutSessions.ts
|       |   |   |   |   |   `-- 20250620121314_add_uppdateIntent_to_subscriptions.ts
|       |   |   |   |   |-- utils/
|       |   |   |   |   |   `-- limits.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- gendo/
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   `-- gendo.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- main.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- types/
|       |   |   |   |   |       |-- graphTypes.ts
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20240522130000_gendo.ts
|       |   |   |   |   |   `-- 20241120140402_gendo_credits.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- index.ts
|       |   |   |   |   |   `-- userCredits.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- multiregion/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   |-- mocks/
|       |   |   |   |   |   |   `-- index.ts
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   |-- index.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   `-- 20241031081827_create_regions_table.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- index.ts
|       |   |   |   |   |   |-- projectRegion.ts
|       |   |   |   |   |   `-- transactions.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- config.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- projectRegion.ts
|       |   |   |   |   |   `-- queue.ts
|       |   |   |   |   |-- tasks/
|       |   |   |   |   |   |-- pendingTransactions.ts
|       |   |   |   |   |   `-- regionSync.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- e2e/
|       |   |   |   |   |   |   |-- projects.graph.spec.ts
|       |   |   |   |   |   |   `-- serverAdmin.graph.spec.ts
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   |-- repositories/
|       |   |   |   |   |   |   |   |-- projectRegion.spec.ts
|       |   |   |   |   |   |   |   `-- transactions.spec.ts
|       |   |   |   |   |   |   `-- sync.spec.ts
|       |   |   |   |   |   |-- unit/
|       |   |   |   |   |   |   `-- projectRegion.spec.ts
|       |   |   |   |   |   `-- helpers.ts
|       |   |   |   |   |-- utils/
|       |   |   |   |   |   |-- blobStorageSelector.ts
|       |   |   |   |   |   |-- dbSelector.ts
|       |   |   |   |   |   `-- regionSelector.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   `-- regionConfig.ts
|       |   |   |   |-- notifications/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   `-- operations.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- userNotificationPreferences.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20220825123323_usernotificationpreferences.ts
|       |   |   |   |   |   `-- 20250915154600_user_notifications.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- handlers/
|       |   |   |   |   |   |   |-- activityDigest.ts
|       |   |   |   |   |   |   |-- mentionedInComment.ts
|       |   |   |   |   |   |   |-- newStreamAccessRequest.ts
|       |   |   |   |   |   |   `-- streamAccessRequestApproved.ts
|       |   |   |   |   |   |-- notificationPreferences.ts
|       |   |   |   |   |   |-- publication.ts
|       |   |   |   |   |   `-- queue.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- activityDigest.spec.ts
|       |   |   |   |   |   |-- notifications.spec.ts
|       |   |   |   |   |   `-- notificationsPreferences.spec.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   `-- repositories.ts
|       |   |   |   |-- previews/
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   `-- bull.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- consts.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- errors.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   `-- 20210426200000-previews.js
|       |   |   |   |   |-- observability/
|       |   |   |   |   |   `-- metrics.ts
|       |   |   |   |   |-- queues/
|       |   |   |   |   |   `-- previews.ts
|       |   |   |   |   |-- repository/
|       |   |   |   |   |   `-- previews.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- router.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- createObjectPreview.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- responses.ts
|       |   |   |   |   |   `-- retryErrors.ts
|       |   |   |   |   |-- tasks/
|       |   |   |   |   |   `-- tasks.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   |-- repository.spec.ts
|       |   |   |   |   |   |   `-- retryErrors.spec.ts
|       |   |   |   |   |   `-- unit/
|       |   |   |   |   |       |-- createObjectPreview.spec.ts
|       |   |   |   |   |       `-- responses.spec.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   |-- ogImage.ts
|       |   |   |   |   `-- resultListener.ts
|       |   |   |   |-- pwdreset/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   `-- operations.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   `-- 20210304111614_pwdreset.js
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- finalize.ts
|       |   |   |   |   |   `-- request.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   `-- pwdrest.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- serverinvites/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- constants.ts
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   `-- subscriptionListeners.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- serverInvites.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- core.ts
|       |   |   |   |   |   `-- graphTypes.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20210303185834_invites.js
|       |   |   |   |   |   |-- 20220629110918_server_invites_rework.js
|       |   |   |   |   |   |-- 20220722092821_add_invite_token_field.js
|       |   |   |   |   |   |-- 20230517122919_clean_up_invalid_stream_invites.ts
|       |   |   |   |   |   |-- 20230818075729_add_invite_server_role_support.ts
|       |   |   |   |   |   |-- 20230907131636_migrate_invites_to_lower_precision_timestamps.ts
|       |   |   |   |   |   |-- 20240716094858_generalized_invite_record_resources.ts
|       |   |   |   |   |   |-- 20240716134617_migrate_to_resources_array.ts
|       |   |   |   |   |   `-- 20240808140602_add_invite_updated_at.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- serverInvites.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- coreEmailContents.ts
|       |   |   |   |   |   |-- coreFinalization.ts
|       |   |   |   |   |   |-- coreResourceCollection.ts
|       |   |   |   |   |   |-- creation.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |-- processing.ts
|       |   |   |   |   |   |-- projectInviteManagement.ts
|       |   |   |   |   |   `-- retrieval.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   `-- invites.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- shared/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- authz/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- rolesAndScopes/
|       |   |   |   |   |   |   |-- logic.ts
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- constants.ts
|       |   |   |   |   |   `-- operations.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   |-- base.ts
|       |   |   |   |   |   |-- databaseMetadata.ts
|       |   |   |   |   |   |-- encryption.ts
|       |   |   |   |   |   |-- ensureError.ts
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- cryptoHelper.ts
|       |   |   |   |   |   |-- dbHelper.ts
|       |   |   |   |   |   |-- envHelper.ts
|       |   |   |   |   |   |-- errorHelper.ts
|       |   |   |   |   |   |-- factory.ts
|       |   |   |   |   |   |-- graphqlHelper.ts
|       |   |   |   |   |   |-- mocks.ts
|       |   |   |   |   |   |-- sanitization.ts
|       |   |   |   |   |   `-- typeHelper.ts
|       |   |   |   |   |-- middleware/
|       |   |   |   |   |   |-- index.ts
|       |   |   |   |   |   `-- security.ts
|       |   |   |   |   |-- redis/
|       |   |   |   |   |   `-- redis.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- acl.ts
|       |   |   |   |   |   |-- roles.ts
|       |   |   |   |   |   `-- scopes.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- auth.ts
|       |   |   |   |   |   |-- eventBus.ts
|       |   |   |   |   |   `-- paginatedItems.ts
|       |   |   |   |   |-- test/
|       |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   `-- mixpanel.ts
|       |   |   |   |   |   |-- unit/
|       |   |   |   |   |   |   |-- eventBus.spec.ts
|       |   |   |   |   |   |   `-- rolesAndScopes.spec.ts
|       |   |   |   |   |   |-- authz.spec.ts
|       |   |   |   |   |   `-- dbHelper.spec.ts
|       |   |   |   |   |-- utils/
|       |   |   |   |   |   |-- caching.spec.ts
|       |   |   |   |   |   |-- caching.ts
|       |   |   |   |   |   |-- ip.ts
|       |   |   |   |   |   |-- libsodium.ts
|       |   |   |   |   |   |-- mixpanel.ts
|       |   |   |   |   |   `-- subscriptions.ts
|       |   |   |   |   |-- authz.ts
|       |   |   |   |   |-- command.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- stats/
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- stats.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   `-- stats.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- viewer/
|       |   |   |   |   |-- authz/
|       |   |   |   |   |   `-- loaders/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- events/
|       |   |   |   |   |   |   `-- savedViews.ts
|       |   |   |   |   |   |-- operations/
|       |   |   |   |   |   |   |-- resources.ts
|       |   |   |   |   |   |   |-- savedViewGroupApiTokens.ts
|       |   |   |   |   |   |   `-- savedViews.ts
|       |   |   |   |   |   `-- types/
|       |   |   |   |   |       |-- resources.ts
|       |   |   |   |   |       |-- savedViewGroupApiTokens.ts
|       |   |   |   |   |       `-- savedViews.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- savedViews.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   `-- subscriptionListeners.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   |-- dataloaders/
|       |   |   |   |   |   |   `-- index.ts
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       |-- permissions.ts
|       |   |   |   |   |       |-- savedViews.ts
|       |   |   |   |   |       |-- shares.ts
|       |   |   |   |   |       `-- viewerResources.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- graphTypes.ts
|       |   |   |   |   |   `-- savedViews.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20250721102623_add_saved_views_tables.ts
|       |   |   |   |   |   |-- 20250917135031_set_init_manual_positions.ts
|       |   |   |   |   |   |-- 20250923100148_add_saved_view_groups_shares_table.ts
|       |   |   |   |   |   `-- 20250924081359_add_saved_view_thumbnail.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- dataLoaders/
|       |   |   |   |   |   |   `-- savedViews.ts
|       |   |   |   |   |   |-- savedViews.ts
|       |   |   |   |   |   `-- tokens.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- savedViews.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- savedViewPreviews.ts
|       |   |   |   |   |   |-- savedViewsManagement.ts
|       |   |   |   |   |   |-- tokens.ts
|       |   |   |   |   |   `-- viewerResources.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   |-- graphql.ts
|       |   |   |   |   |   |   `-- savedViews.ts
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   |-- savedViewsCrud.graph.spec.ts
|       |   |   |   |   |   |   `-- viewerResources.spec.ts
|       |   |   |   |   |   `-- unit/
|       |   |   |   |   |       `-- tokens.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- webhooks/
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- webhooks.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       `-- webhooks.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- graphTypes.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20210701180000-webhooks.js
|       |   |   |   |   |   |-- 20221104104921_webhooks_drop_stream_fk.ts
|       |   |   |   |   |   `-- 20230919080704_add_webhook_config_timestamps.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- cleanup.ts
|       |   |   |   |   |   `-- webhooks.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   `-- webhooks.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- cleanup.spec.ts
|       |   |   |   |   |   `-- webhooks.spec.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- workspaces/
|       |   |   |   |   |-- authz/
|       |   |   |   |   |   `-- loaders/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- clients/
|       |   |   |   |   |   `-- oidcProvider.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- sso/
|       |   |   |   |   |   |   |-- logic.ts
|       |   |   |   |   |   |   |-- models.ts
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- constants.ts
|       |   |   |   |   |   |-- logic.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   |-- regions.ts
|       |   |   |   |   |   |-- sso.ts
|       |   |   |   |   |   |-- workspace.ts
|       |   |   |   |   |   `-- workspaceSeat.ts
|       |   |   |   |   |-- events/
|       |   |   |   |   |   `-- eventListener.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   |-- dataloaders/
|       |   |   |   |   |   |   `-- workspaces.ts
|       |   |   |   |   |   |-- directives/
|       |   |   |   |   |   |   `-- hasWorkspaceRole.ts
|       |   |   |   |   |   |-- mocks/
|       |   |   |   |   |   |   `-- workspaces.ts
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       |-- permissions.ts
|       |   |   |   |   |       |-- projects.ts
|       |   |   |   |   |       |-- regions.ts
|       |   |   |   |   |       |-- workspaceJoinRequests.ts
|       |   |   |   |   |       `-- workspaces.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- db.ts
|       |   |   |   |   |   |-- images.spec.ts
|       |   |   |   |   |   |-- images.ts
|       |   |   |   |   |   |-- roles.ts
|       |   |   |   |   |   `-- sso.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- projectRegions.ts
|       |   |   |   |   |   |-- projects.ts
|       |   |   |   |   |   |-- regions.ts
|       |   |   |   |   |   |-- sso.ts
|       |   |   |   |   |   |-- users.ts
|       |   |   |   |   |   |-- workspaceJoinRequests.ts
|       |   |   |   |   |   `-- workspaces.ts
|       |   |   |   |   |-- rest/
|       |   |   |   |   |   `-- sso.ts
|       |   |   |   |   |-- services/
|       |   |   |   |   |   |-- workspaceJoinRequestEmails/
|       |   |   |   |   |   |   |-- approved.ts
|       |   |   |   |   |   |   |-- denied.ts
|       |   |   |   |   |   |   `-- received.ts
|       |   |   |   |   |   |-- domains.ts
|       |   |   |   |   |   |-- invites.ts
|       |   |   |   |   |   |-- management.ts
|       |   |   |   |   |   |-- projectRegions.ts
|       |   |   |   |   |   |-- projects.ts
|       |   |   |   |   |   |-- regions.ts
|       |   |   |   |   |   |-- retrieval.ts
|       |   |   |   |   |   |-- sso.ts
|       |   |   |   |   |   |-- tracking.ts
|       |   |   |   |   |   |-- workspaceCreationState.ts
|       |   |   |   |   |   |-- workspaceJoinRequests.ts
|       |   |   |   |   |   |-- workspaceLimits.ts
|       |   |   |   |   |   `-- workspaceSeat.ts
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- helpers/
|       |   |   |   |   |   |   |-- creation.ts
|       |   |   |   |   |   |   |-- graphql.ts
|       |   |   |   |   |   |   |-- invites.ts
|       |   |   |   |   |   |   `-- rolesGraphql.ts
|       |   |   |   |   |   |-- integration/
|       |   |   |   |   |   |   |-- repositories/
|       |   |   |   |   |   |   |   |-- projects.spec.ts
|       |   |   |   |   |   |   |   |-- users.spec.ts
|       |   |   |   |   |   |   |   `-- workspaces.spec.ts
|       |   |   |   |   |   |   |-- invites.graph.spec.ts
|       |   |   |   |   |   |   |-- projects.graph.spec.ts
|       |   |   |   |   |   |   |-- regions.graph.spec.ts
|       |   |   |   |   |   |   |-- repositories.spec.ts
|       |   |   |   |   |   |   |-- roles.graph.spec.ts
|       |   |   |   |   |   |   |-- sso.graph.spec.ts
|       |   |   |   |   |   |   |-- sso.spec.ts
|       |   |   |   |   |   |   |-- subs.graph.spec.ts
|       |   |   |   |   |   |   |-- tracking.spec.ts
|       |   |   |   |   |   |   |-- users.graph.spec.ts
|       |   |   |   |   |   |   |-- workspaceJoinRequests.graph.spec.ts
|       |   |   |   |   |   |   |-- workspaceJoinRequests.spec.ts
|       |   |   |   |   |   |   |-- workspaces.graph.spec.ts
|       |   |   |   |   |   |   |-- workspacesCreationState.spec.ts
|       |   |   |   |   |   |   |-- workspaceSeat.graph.spec.ts
|       |   |   |   |   |   |   `-- workspaceSeat.spec.ts
|       |   |   |   |   |   `-- unit/
|       |   |   |   |   |       |-- domain/
|       |   |   |   |   |       |   `-- logic.spec.ts
|       |   |   |   |   |       |-- events/
|       |   |   |   |   |       |   `-- eventListener.spec.ts
|       |   |   |   |   |       |-- helpers/
|       |   |   |   |   |       |   `-- sso.spec.ts
|       |   |   |   |   |       |-- services/
|       |   |   |   |   |       |   |-- domains.spec.ts
|       |   |   |   |   |       |   |-- management.spec.ts
|       |   |   |   |   |       |   |-- projects.spec.ts
|       |   |   |   |   |       |   |-- sso.spec.ts
|       |   |   |   |   |       |   `-- workspaceSeat.spec.ts
|       |   |   |   |   |       `-- utils/
|       |   |   |   |   |           `-- roles.spec.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   |-- LICENSE
|       |   |   |   |   |-- roles.ts
|       |   |   |   |   `-- scopes.ts
|       |   |   |   |-- workspacesCore/
|       |   |   |   |   |-- authz/
|       |   |   |   |   |   `-- loaders/
|       |   |   |   |   |       `-- index.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- constants.ts
|       |   |   |   |   |   |-- events.ts
|       |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- graph/
|       |   |   |   |   |   `-- resolvers/
|       |   |   |   |   |       |-- workspaceJoinRequests.ts
|       |   |   |   |   |       `-- workspacesCore.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- db.ts
|       |   |   |   |   |   |-- graphHelpers.ts
|       |   |   |   |   |   `-- graphTypes.ts
|       |   |   |   |   |-- migrations/
|       |   |   |   |   |   |-- 20240621174016_workspaces.ts
|       |   |   |   |   |   |-- 20240628112300_dropCreatorId.ts
|       |   |   |   |   |   |-- 20240801000000_logos.ts
|       |   |   |   |   |   |-- 20240802212846_cascadeDeleteWorkspaceProjects.ts
|       |   |   |   |   |   |-- 20240806160740_workspace_domains.ts
|       |   |   |   |   |   |-- 20240807174901_add_column_domainBasedMembershipProtection.ts
|       |   |   |   |   |   |-- 20240808091944_add_workspace_discovery_flag.ts
|       |   |   |   |   |   |-- 20240813125251_workspaceAclWithTimestamps.ts
|       |   |   |   |   |   |-- 20240820131619_fallbackWorkspaceLogo.ts
|       |   |   |   |   |   |-- 20240910163614_add_column_defaultProjectRole.ts
|       |   |   |   |   |   |-- 20240912134548_add_workspace_slug.ts
|       |   |   |   |   |   |-- 20240926112407_copy_workspace_slug.ts
|       |   |   |   |   |   |-- 20240930141322_workspace_sso.ts
|       |   |   |   |   |   |-- 20241014092507_workspace_sso_expiration.ts
|       |   |   |   |   |   |-- 20241105070219_create_workspace_regions_table.ts
|       |   |   |   |   |   |-- 20241128153315_workspace_creation_state.ts
|       |   |   |   |   |   |-- 20241202183039_workspace_start_trial.ts
|       |   |   |   |   |   |-- 20241220093308_create_workspace_join_requests_table.ts
|       |   |   |   |   |   |-- 20250127110735_drop_default_logo_index.ts
|       |   |   |   |   |   |-- 20250219100906_index_user_id_workspace_join_requests.ts
|       |   |   |   |   |   |-- 20250319092538_remove_defaultProjectRole.ts
|       |   |   |   |   |   |-- 20250514092509_add_missing_seats.ts
|       |   |   |   |   |   |-- 20250516130608_add_workspace_embed_options.ts
|       |   |   |   |   |   |-- 20250521100349_add_discoverable_workspace_auto_join.ts
|       |   |   |   |   |   |-- 20250606043717_add_exclusive_workspace_option.ts
|       |   |   |   |   |   |-- 20250820151448_add_sso_timeout_override.ts
|       |   |   |   |   |   |-- 20250822161233_workspace_feature_flags.ts
|       |   |   |   |   |   `-- 20250905074349_drop_workspace_defaults.ts
|       |   |   |   |   |-- repositories/
|       |   |   |   |   |   |-- rolesSeats.ts
|       |   |   |   |   |   `-- workspaces.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- index.ts
|       |   |   |   |-- loaders.ts
|       |   |   |   `-- mocks.ts
|       |   |   |-- observability/
|       |   |   |   |-- components/
|       |   |   |   |   |-- apollo/
|       |   |   |   |   |   |-- metrics/
|       |   |   |   |   |   |   `-- apolloSubscriptionMonitoring.ts
|       |   |   |   |   |   `-- apolloSubscriptions.ts
|       |   |   |   |   |-- express/
|       |   |   |   |   |   |-- metrics/
|       |   |   |   |   |   |   `-- errorMetrics.ts
|       |   |   |   |   |   |-- expressLogging.ts
|       |   |   |   |   |   `-- requestContextMiddleware.ts
|       |   |   |   |   |-- highFrequencyMetrics/
|       |   |   |   |   |   |-- heapSizeAndUsed.ts
|       |   |   |   |   |   |-- highfrequencyMonitoring.ts
|       |   |   |   |   |   |-- knexConnectionPool.ts
|       |   |   |   |   |   `-- processCPUTotal.ts
|       |   |   |   |   |-- httpServer/
|       |   |   |   |   |   `-- httpServerMonitoring.ts
|       |   |   |   |   `-- knex/
|       |   |   |   |       `-- knexMonitoring.ts
|       |   |   |   |-- domain/
|       |   |   |   |   |-- businessLogging.ts
|       |   |   |   |   `-- fields.ts
|       |   |   |   |-- tests/
|       |   |   |   |   `-- metrics.spec.ts
|       |   |   |   |-- utils/
|       |   |   |   |   |-- logLevels.ts
|       |   |   |   |   |-- machineId.ts
|       |   |   |   |   |-- redact.spec.ts
|       |   |   |   |   |-- redact.ts
|       |   |   |   |   `-- requestContext.ts
|       |   |   |   |-- index.ts
|       |   |   |   |-- logging.ts
|       |   |   |   `-- otel.ts
|       |   |   |-- packages/
|       |   |   |   `-- server/
|       |   |   |       |-- assets/
|       |   |   |       |   `-- elementsquery/
|       |   |   |       |       `-- typedefs/
|       |   |   |       |           `-- elementsQuery.graphql
|       |   |   |       `-- modules/
|       |   |   |           `-- elementsquery/
|       |   |   |               |-- graph/
|       |   |   |               |   `-- resolvers/
|       |   |   |               |       `-- elementsQuery.ts
|       |   |   |               |-- migrations/
|       |   |   |               |   |-- .gitkeep
|       |   |   |               |   `-- 20250130000000_create_elements_queryable.ts
|       |   |   |               |-- repositories/
|       |   |   |               |   `-- elementsQuery.ts
|       |   |   |               |-- dbSchema.ts
|       |   |   |               `-- index.ts
|       |   |   |-- scripts/
|       |   |   |   |-- duplicateUserMigration.ts
|       |   |   |   |-- moveProjectsBetweenServers.ts
|       |   |   |   |-- seedUsers.ts
|       |   |   |   `-- streamObjects.ts
|       |   |   |-- test/
|       |   |   |   |-- assets/
|       |   |   |   |   `-- automate/
|       |   |   |   |       `-- encryptionKeys.json
|       |   |   |   |-- graphql/
|       |   |   |   |   |-- accessRequests.ts
|       |   |   |   |   |-- apiTokens.ts
|       |   |   |   |   |-- automate.ts
|       |   |   |   |   |-- comments.ts
|       |   |   |   |   |-- commits.ts
|       |   |   |   |   |-- core.ts
|       |   |   |   |   |-- embedTokens.ts
|       |   |   |   |   |-- gatekeeper.ts
|       |   |   |   |   |-- models.ts
|       |   |   |   |   |-- multiRegion.ts
|       |   |   |   |   |-- projectAccessRequests.ts
|       |   |   |   |   |-- projectComments.ts
|       |   |   |   |   |-- projects.ts
|       |   |   |   |   |-- serverInvites.ts
|       |   |   |   |   |-- streams.ts
|       |   |   |   |   |-- userEmails.ts
|       |   |   |   |   |-- users.ts
|       |   |   |   |   |-- versions.ts
|       |   |   |   |   `-- workspaces.ts
|       |   |   |   |-- mocks/
|       |   |   |   |   `-- global.ts
|       |   |   |   |-- plugins/
|       |   |   |   |   `-- graphql.ts
|       |   |   |   |-- speckle-helpers/
|       |   |   |   |   |-- activityStreamHelper.ts
|       |   |   |   |   |-- automationHelper.ts
|       |   |   |   |   |-- blobHelper.ts
|       |   |   |   |   |-- branchHelper.ts
|       |   |   |   |   |-- commentHelper.ts
|       |   |   |   |   |-- commitHelper.ts
|       |   |   |   |   |-- email.ts
|       |   |   |   |   |-- error.ts
|       |   |   |   |   |-- inviteHelper.ts
|       |   |   |   |   |-- regions.ts
|       |   |   |   |   |-- streamHelper.ts
|       |   |   |   |   `-- workspaces.ts
|       |   |   |   |-- assertionHelper.ts
|       |   |   |   |-- authHelper.ts
|       |   |   |   |-- blobHelper.ts
|       |   |   |   |-- graphqlHelper.ts
|       |   |   |   |-- helpers.ts
|       |   |   |   |-- hooks.ts
|       |   |   |   |-- notificationsHelper.ts
|       |   |   |   |-- projectHelper.ts
|       |   |   |   |-- redisHelper.ts
|       |   |   |   `-- serverHelper.ts
|       |   |   |-- type-augmentations/
|       |   |   |   |-- acc.d.ts
|       |   |   |   |-- chai.d.ts
|       |   |   |   |-- express.d.ts
|       |   |   |   |-- knex.d.ts
|       |   |   |   `-- verror.d.ts
|       |   |   |-- .c8rc.json
|       |   |   |-- .env.example
|       |   |   |-- .env.test-example
|       |   |   |-- .mocharc.cjs
|       |   |   |-- app.ts
|       |   |   |-- AWS_INFRASTRUCTURE_OVERVIEW.md
|       |   |   |-- bootstrap.js
|       |   |   |-- codegen.ts
|       |   |   |-- Dockerfile
|       |   |   |-- ENV_SETUP.md
|       |   |   |-- eslint.config.mjs
|       |   |   |-- esmLoader.js
|       |   |   |-- extract_render_materials.py
|       |   |   |-- feature_flags.md
|       |   |   |-- knexfile.ts
|       |   |   |-- multiregion.example.json
|       |   |   |-- multiregion.test.example.json
|       |   |   |-- nodemon.json
|       |   |   |-- package.json
|       |   |   |-- pgadmin-deployment.yaml
|       |   |   |-- pgadmin-ingress.yaml
|       |   |   |-- QUICK_START_TESTING.md
|       |   |   |-- readme.md
|       |   |   |-- root.js
|       |   |   |-- run.ts
|       |   |   |-- SPECKLE_OBJECT_ARCHITECTURE.md
|       |   |   |-- TESTING_QUICK.md
|       |   |   |-- tsconfig.build.json
|       |   |   `-- tsconfig.json
|       |   |-- shared/
|       |   |   |-- e2e/
|       |   |   |   |-- testCjs.cjs
|       |   |   |   `-- testEsm.mjs
|       |   |   |-- src/
|       |   |   |   |-- acc/
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- authz/
|       |   |   |   |   |-- checks/
|       |   |   |   |   |   |-- dashboards.spec.ts
|       |   |   |   |   |   |-- dashboards.ts
|       |   |   |   |   |   |-- projects.spec.ts
|       |   |   |   |   |   |-- projects.ts
|       |   |   |   |   |   |-- serverRole.spec.ts
|       |   |   |   |   |   |-- serverRole.ts
|       |   |   |   |   |   |-- workspaceRole.spec.ts
|       |   |   |   |   |   |-- workspaceRole.ts
|       |   |   |   |   |   |-- workspaceSeat.spec.ts
|       |   |   |   |   |   `-- workspaceSeat.ts
|       |   |   |   |   |-- domain/
|       |   |   |   |   |   |-- automate/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- comments/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- core/
|       |   |   |   |   |   |   `-- operations.ts
|       |   |   |   |   |   |-- dashboards/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- logic/
|       |   |   |   |   |   |   |-- roles.spec.ts
|       |   |   |   |   |   |   `-- roles.ts
|       |   |   |   |   |   |-- models/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- projects/
|       |   |   |   |   |   |   |-- limits.ts
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- savedViews/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- versions/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- workspaces/
|       |   |   |   |   |   |   |-- operations.ts
|       |   |   |   |   |   |   `-- types.ts
|       |   |   |   |   |   |-- authErrors.ts
|       |   |   |   |   |   |-- context.ts
|       |   |   |   |   |   |-- errors.ts
|       |   |   |   |   |   |-- loaders.ts
|       |   |   |   |   |   `-- policies.ts
|       |   |   |   |   |-- fragments/
|       |   |   |   |   |   |-- automate.spec.ts
|       |   |   |   |   |   |-- automate.ts
|       |   |   |   |   |   |-- dashboards.ts
|       |   |   |   |   |   |-- projects.spec.ts
|       |   |   |   |   |   |-- projects.ts
|       |   |   |   |   |   |-- savedViews.spec.ts
|       |   |   |   |   |   |-- savedViews.ts
|       |   |   |   |   |   |-- server.spec.ts
|       |   |   |   |   |   |-- server.ts
|       |   |   |   |   |   |-- workspaces.spec.ts
|       |   |   |   |   |   `-- workspaces.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- graphql.ts
|       |   |   |   |   |-- policies/
|       |   |   |   |   |   |-- automate/
|       |   |   |   |   |   |   `-- function/
|       |   |   |   |   |   |       |-- canEditFunction.spec.ts
|       |   |   |   |   |   |       `-- canEditFunction.ts
|       |   |   |   |   |   |-- dashboard/
|       |   |   |   |   |   |   |-- canCreateToken.ts
|       |   |   |   |   |   |   |-- canDelete.ts
|       |   |   |   |   |   |   |-- canEdit.ts
|       |   |   |   |   |   |   `-- canRead.ts
|       |   |   |   |   |   |-- project/
|       |   |   |   |   |   |   |-- automation/
|       |   |   |   |   |   |   |   |-- canCreate.spec.ts
|       |   |   |   |   |   |   |   |-- canCreate.ts
|       |   |   |   |   |   |   |   |-- canDelete.spec.ts
|       |   |   |   |   |   |   |   |-- canDelete.ts
|       |   |   |   |   |   |   |   |-- canRead.spec.ts
|       |   |   |   |   |   |   |   |-- canRead.ts
|       |   |   |   |   |   |   |   |-- canUpdate.spec.ts
|       |   |   |   |   |   |   |   `-- canUpdate.ts
|       |   |   |   |   |   |   |-- comment/
|       |   |   |   |   |   |   |   |-- canArchive.spec.ts
|       |   |   |   |   |   |   |   |-- canArchive.ts
|       |   |   |   |   |   |   |   |-- canCreate.spec.ts
|       |   |   |   |   |   |   |   |-- canCreate.ts
|       |   |   |   |   |   |   |   |-- canEdit.spec.ts
|       |   |   |   |   |   |   |   `-- canEdit.ts
|       |   |   |   |   |   |   |-- model/
|       |   |   |   |   |   |   |   |-- canCreate.spec.ts
|       |   |   |   |   |   |   |   |-- canCreate.ts
|       |   |   |   |   |   |   |   |-- canDelete.spec.ts
|       |   |   |   |   |   |   |   |-- canDelete.ts
|       |   |   |   |   |   |   |   |-- canUpdate.spec.ts
|       |   |   |   |   |   |   |   `-- canUpdate.ts
|       |   |   |   |   |   |   |-- savedViews/
|       |   |   |   |   |   |   |   |-- canCreate.spec.ts
|       |   |   |   |   |   |   |   |-- canCreate.ts
|       |   |   |   |   |   |   |   |-- canCreateSavedViewGroupToken.spec.ts
|       |   |   |   |   |   |   |   |-- canCreateSavedViewGroupToken.ts
|       |   |   |   |   |   |   |   |-- canEditDescription.spec.ts
|       |   |   |   |   |   |   |   |-- canEditDescription.ts
|       |   |   |   |   |   |   |   |-- canEditTitle.spec.ts
|       |   |   |   |   |   |   |   |-- canEditTitle.ts
|       |   |   |   |   |   |   |   |-- canMove.spec.ts
|       |   |   |   |   |   |   |   |-- canMove.ts
|       |   |   |   |   |   |   |   |-- canRead.ts
|       |   |   |   |   |   |   |   |-- canSetAsHomeView.spec.ts
|       |   |   |   |   |   |   |   |-- canSetAsHomeView.ts
|       |   |   |   |   |   |   |   |-- canUpdate.spec.ts
|       |   |   |   |   |   |   |   |-- canUpdate.ts
|       |   |   |   |   |   |   |   |-- canUpdateGroup.spec.ts
|       |   |   |   |   |   |   |   `-- canUpdateGroup.ts
|       |   |   |   |   |   |   |-- version/
|       |   |   |   |   |   |   |   |-- canCreate.spec.ts
|       |   |   |   |   |   |   |   |-- canCreate.ts
|       |   |   |   |   |   |   |   |-- canRequestRender.spec.ts
|       |   |   |   |   |   |   |   |-- canRequestRender.ts
|       |   |   |   |   |   |   |   |-- canUpdate.spec.ts
|       |   |   |   |   |   |   |   `-- canUpdate.ts
|       |   |   |   |   |   |   |-- canBroadcastActivity.spec.ts
|       |   |   |   |   |   |   |-- canBroadcastActivity.ts
|       |   |   |   |   |   |   |-- canCreatePersonal.spec.ts
|       |   |   |   |   |   |   |-- canCreatePersonal.ts
|       |   |   |   |   |   |   |-- canDelete.spec.ts
|       |   |   |   |   |   |   |-- canDelete.ts
|       |   |   |   |   |   |   |-- canInvite.spec.ts
|       |   |   |   |   |   |   |-- canInvite.ts
|       |   |   |   |   |   |   |-- canLeave.spec.ts
|       |   |   |   |   |   |   |-- canLeave.ts
|       |   |   |   |   |   |   |-- canLoad.spec.ts
|       |   |   |   |   |   |   |-- canLoad.ts
|       |   |   |   |   |   |   |-- canMoveToWorkspace.spec.ts
|       |   |   |   |   |   |   |-- canMoveToWorkspace.ts
|       |   |   |   |   |   |   |-- canPublish.spec.ts
|       |   |   |   |   |   |   |-- canPublish.ts
|       |   |   |   |   |   |   |-- canRead.spec.ts
|       |   |   |   |   |   |   |-- canRead.ts
|       |   |   |   |   |   |   |-- canReadAccIntegrationSettings.spec.ts
|       |   |   |   |   |   |   |-- canReadAccIntegrationSettings.ts
|       |   |   |   |   |   |   |-- canReadSettings.spec.ts
|       |   |   |   |   |   |   |-- canReadSettings.ts
|       |   |   |   |   |   |   |-- canReadWebhooks.spec.ts
|       |   |   |   |   |   |   |-- canReadWebhooks.ts
|       |   |   |   |   |   |   |-- canUpdate.spec.ts
|       |   |   |   |   |   |   |-- canUpdate.ts
|       |   |   |   |   |   |   |-- canUpdateAllowPublicComments.spec.ts
|       |   |   |   |   |   |   |-- canUpdateAllowPublicComments.ts
|       |   |   |   |   |   |   |-- canUpdateEmbedTokens.spec.ts
|       |   |   |   |   |   |   `-- canUpdateEmbedTokens.ts
|       |   |   |   |   |   |-- workspace/
|       |   |   |   |   |   |   |-- canCreateDashboards.ts
|       |   |   |   |   |   |   |-- canCreateWorkspace.spec.ts
|       |   |   |   |   |   |   |-- canCreateWorkspace.ts
|       |   |   |   |   |   |   |-- canCreateWorkspaceProject.spec.ts
|       |   |   |   |   |   |   |-- canCreateWorkspaceProject.ts
|       |   |   |   |   |   |   |-- canInvite.ts
|       |   |   |   |   |   |   |-- canListDashboards.ts
|       |   |   |   |   |   |   |-- canReadMemberEmail.spec.ts
|       |   |   |   |   |   |   |-- canReadMemberEmail.ts
|       |   |   |   |   |   |   |-- canReceiveProjectsUpdatedMessage.spec.ts
|       |   |   |   |   |   |   |-- canReceiveProjectsUpdatedMessage.ts
|       |   |   |   |   |   |   |-- canUseWorkspacePlanFeature.spec.ts
|       |   |   |   |   |   |   `-- canUseWorkspacePlanFeature.ts
|       |   |   |   |   |   |-- index.spec.ts
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- automate/
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- types.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- blobs/
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- core/
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- batch.ts
|       |   |   |   |   |   |-- debugging.ts
|       |   |   |   |   |   |-- encoding.ts
|       |   |   |   |   |   |-- error.spec.ts
|       |   |   |   |   |   |-- error.ts
|       |   |   |   |   |   |-- optimization.ts
|       |   |   |   |   |   |-- os.ts
|       |   |   |   |   |   |-- timeConstants.ts
|       |   |   |   |   |   |-- tracking.ts
|       |   |   |   |   |   |-- url.ts
|       |   |   |   |   |   |-- utility.spec.ts
|       |   |   |   |   |   |-- utility.ts
|       |   |   |   |   |   `-- utilityTypes.ts
|       |   |   |   |   |-- utils/
|       |   |   |   |   |   |-- base64.spec.ts
|       |   |   |   |   |   |-- base64.ts
|       |   |   |   |   |   |-- localStorage.ts
|       |   |   |   |   |   |-- md5.spec.ts
|       |   |   |   |   |   `-- md5.ts
|       |   |   |   |   |-- constants.spec.ts
|       |   |   |   |   |-- constants.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- environment/
|       |   |   |   |   |-- db.spec.ts
|       |   |   |   |   |-- db.ts
|       |   |   |   |   |-- featureFlags.ts
|       |   |   |   |   |-- index.spec.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   `-- node.ts
|       |   |   |   |-- images/
|       |   |   |   |   |-- base64.spec.ts
|       |   |   |   |   `-- base64.ts
|       |   |   |   |-- limit/
|       |   |   |   |   |-- domain.ts
|       |   |   |   |   |-- utils.spec.ts
|       |   |   |   |   `-- utils.ts
|       |   |   |   |-- observability/
|       |   |   |   |   |-- index.ts
|       |   |   |   |   |-- mixpanel.ts
|       |   |   |   |   `-- pinoClef.ts
|       |   |   |   |-- onboarding/
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- queue/
|       |   |   |   |   |-- config.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- redis/
|       |   |   |   |   |-- index.ts
|       |   |   |   |   `-- isRedisReady.ts
|       |   |   |   |-- rich-text-editor/
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- saved-views/
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- defaultGroup.spec.ts
|       |   |   |   |   |   `-- defaultGroup.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- tests/
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- types.ts
|       |   |   |   |   |   `-- utils.ts
|       |   |   |   |   |-- fakes.ts
|       |   |   |   |   `-- setup.ts
|       |   |   |   |-- viewer/
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- route.spec.ts
|       |   |   |   |   |   |-- route.ts
|       |   |   |   |   |   |-- state.spec.ts
|       |   |   |   |   |   `-- state.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   |-- workers/
|       |   |   |   |   |-- fileimport/
|       |   |   |   |   |   |-- index.ts
|       |   |   |   |   |   `-- job.ts
|       |   |   |   |   |-- previews/
|       |   |   |   |   |   |-- index.ts
|       |   |   |   |   |   |-- interface.ts
|       |   |   |   |   |   `-- job.ts
|       |   |   |   |   |-- index.ts
|       |   |   |   |   `-- state.ts
|       |   |   |   |-- workspaces/
|       |   |   |   |   |-- errors/
|       |   |   |   |   |   `-- index.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- features.spec.ts
|       |   |   |   |   |   |-- features.ts
|       |   |   |   |   |   |-- limits.ts
|       |   |   |   |   |   |-- plans.spec.ts
|       |   |   |   |   |   `-- plans.ts
|       |   |   |   |   `-- index.ts
|       |   |   |   `-- index.ts
|       |   |   |-- .gitignore
|       |   |   |-- eslint.config.mjs
|       |   |   |-- package.json
|       |   |   |-- pinoPrettyTransport.cjs
|       |   |   |-- readme.md
|       |   |   |-- tsconfig.json
|       |   |   `-- vitest.config.ts
|       |   |-- tailwind-theme/
|       |   |   |-- fonts/
|       |   |   |   |-- inter-cyrillic-ext.woff2
|       |   |   |   |-- inter-cyrillic.woff2
|       |   |   |   |-- inter-greek-ext.woff2
|       |   |   |   |-- inter-greek.woff2
|       |   |   |   |-- inter-latin-ext.woff2
|       |   |   |   |-- inter-latin.woff2
|       |   |   |   |-- inter-vietnamese.woff2
|       |   |   |   `-- license.txt
|       |   |   |-- src/
|       |   |   |   |-- index.ts
|       |   |   |   |-- plugin.ts
|       |   |   |   `-- preset.ts
|       |   |   |-- utils/
|       |   |   |   |-- tailwind-configure.cjs
|       |   |   |   |-- tailwind-configure.d.ts
|       |   |   |   `-- tailwind-configure.js
|       |   |   |-- eslint.config.mjs
|       |   |   |-- package.json
|       |   |   |-- README.md
|       |   |   |-- tailwind.test.config.cjs
|       |   |   |-- tsconfig.cjs.json
|       |   |   `-- tsconfig.json
|       |   |-- ui-components/
|       |   |   |-- .cursor/
|       |   |   |   `-- rules/
|       |   |   |       `-- component-library.mdc
|       |   |   |-- .storybook/
|       |   |   |   |-- main.ts
|       |   |   |   `-- preview.ts
|       |   |   |-- src/
|       |   |   |   |-- assets/
|       |   |   |   |   |-- setup/
|       |   |   |   |   |   `-- mentions.css
|       |   |   |   |   `-- tailwind.css
|       |   |   |   |-- components/
|       |   |   |   |   |-- common/
|       |   |   |   |   |   |-- animation/
|       |   |   |   |   |   |   |-- ClickIcon.vue
|       |   |   |   |   |   |   |-- Instructional.stories.ts
|       |   |   |   |   |   |   |-- Instructional.vue
|       |   |   |   |   |   |   `-- MouseIcon.vue
|       |   |   |   |   |   |-- loading/
|       |   |   |   |   |   |   |-- Bar.stories.ts
|       |   |   |   |   |   |   |-- Bar.vue
|       |   |   |   |   |   |   |-- Icon.stories.ts
|       |   |   |   |   |   |   `-- Icon.vue
|       |   |   |   |   |   |-- steps/
|       |   |   |   |   |   |   |-- Bullet.stories.ts
|       |   |   |   |   |   |   |-- Bullet.vue
|       |   |   |   |   |   |   |-- Number.stories.ts
|       |   |   |   |   |   |   `-- Number.vue
|       |   |   |   |   |   |-- text/
|       |   |   |   |   |   |   |-- Link.stories.ts
|       |   |   |   |   |   |   `-- Link.vue
|       |   |   |   |   |   |-- Alert.stories.ts
|       |   |   |   |   |   |-- Alert.vue
|       |   |   |   |   |   |-- Badge.stories.ts
|       |   |   |   |   |   |-- Badge.vue
|       |   |   |   |   |   |-- ProgressBar.stories.ts
|       |   |   |   |   |   |-- ProgressBar.vue
|       |   |   |   |   |   |-- PromoAlert.stories.ts
|       |   |   |   |   |   |-- PromoAlert.vue
|       |   |   |   |   |   |-- VimeoEmbed.stories.ts
|       |   |   |   |   |   `-- VimeoEmbed.vue
|       |   |   |   |   |-- form/
|       |   |   |   |   |   |-- file-upload/
|       |   |   |   |   |   |   `-- Zone.vue
|       |   |   |   |   |   |-- select/
|       |   |   |   |   |   |   |-- Badges.stories.ts
|       |   |   |   |   |   |   |-- Badges.vue
|       |   |   |   |   |   |   |-- Base.stories.ts
|       |   |   |   |   |   |   |-- Base.vue
|       |   |   |   |   |   |   |-- Multi.stories.ts
|       |   |   |   |   |   |   |-- Multi.vue
|       |   |   |   |   |   |   |-- SourceApps.stories.ts
|       |   |   |   |   |   |   `-- SourceApps.vue
|       |   |   |   |   |   |-- tags/
|       |   |   |   |   |   |   `-- ContextManager.vue
|       |   |   |   |   |   |-- Button.stories.ts
|       |   |   |   |   |   |-- Button.vue
|       |   |   |   |   |   |-- CardButton.stories.ts
|       |   |   |   |   |   |-- CardButton.vue
|       |   |   |   |   |   |-- Checkbox.stories.ts
|       |   |   |   |   |   |-- Checkbox.vue
|       |   |   |   |   |   |-- ClipboardInput.stories.ts
|       |   |   |   |   |   |-- ClipboardInput.vue
|       |   |   |   |   |   |-- CodeInput.stories.ts
|       |   |   |   |   |   |-- CodeInput.vue
|       |   |   |   |   |   |-- DualRange.stories.ts
|       |   |   |   |   |   |-- DualRange.vue
|       |   |   |   |   |   |-- Radio.stories.ts
|       |   |   |   |   |   |-- Radio.vue
|       |   |   |   |   |   |-- RadioGroup.stories.ts
|       |   |   |   |   |   |-- RadioGroup.vue
|       |   |   |   |   |   |-- Range.stories.ts
|       |   |   |   |   |   |-- Range.vue
|       |   |   |   |   |   |-- Switch.stories.ts
|       |   |   |   |   |   |-- Switch.vue
|       |   |   |   |   |   |-- Tags.stories.ts
|       |   |   |   |   |   |-- Tags.vue
|       |   |   |   |   |   |-- TextArea.stories.ts
|       |   |   |   |   |   |-- TextArea.vue
|       |   |   |   |   |   |-- TextInput.stories.ts
|       |   |   |   |   |   `-- TextInput.vue
|       |   |   |   |   |-- global/
|       |   |   |   |   |   |-- icon/
|       |   |   |   |   |   |   |-- Arrow.vue
|       |   |   |   |   |   |   |-- ArrowFilled.vue
|       |   |   |   |   |   |   |-- Check.vue
|       |   |   |   |   |   |   |-- Edit.vue
|       |   |   |   |   |   |   |-- Play.vue
|       |   |   |   |   |   |   `-- Plus.vue
|       |   |   |   |   |   |-- ToastRenderer.stories.ts
|       |   |   |   |   |   `-- ToastRenderer.vue
|       |   |   |   |   |-- layout/
|       |   |   |   |   |   |-- sidebar/
|       |   |   |   |   |   |   |-- menu/
|       |   |   |   |   |   |   |   |-- group/
|       |   |   |   |   |   |   |   |   |-- Group.vue
|       |   |   |   |   |   |   |   |   `-- Item.vue
|       |   |   |   |   |   |   |   `-- Menu.vue
|       |   |   |   |   |   |   |-- Promo.vue
|       |   |   |   |   |   |   |-- Sidebar.stories.ts
|       |   |   |   |   |   |   `-- Sidebar.vue
|       |   |   |   |   |   |-- tabs/
|       |   |   |   |   |   |   |-- Horizontal.stories.ts
|       |   |   |   |   |   |   |-- Horizontal.vue
|       |   |   |   |   |   |   |-- Vertical.stories.ts
|       |   |   |   |   |   |   `-- Vertical.vue
|       |   |   |   |   |   |-- Dialog.stories.ts
|       |   |   |   |   |   |-- Dialog.vue
|       |   |   |   |   |   |-- DialogSection.stories.ts
|       |   |   |   |   |   |-- DialogSection.vue
|       |   |   |   |   |   |-- Disclosure.stories.ts
|       |   |   |   |   |   |-- Disclosure.vue
|       |   |   |   |   |   |-- GridListToggle.stories.ts
|       |   |   |   |   |   |-- GridListToggle.vue
|       |   |   |   |   |   |-- Menu.stories.ts
|       |   |   |   |   |   |-- Menu.vue
|       |   |   |   |   |   |-- Panel.stories.ts
|       |   |   |   |   |   |-- Panel.vue
|       |   |   |   |   |   |-- Table.stories.ts
|       |   |   |   |   |   `-- Table.vue
|       |   |   |   |   |-- user/
|       |   |   |   |   |   |-- Avatar.stories.ts
|       |   |   |   |   |   |-- Avatar.vue
|       |   |   |   |   |   |-- AvatarEditable.stories.ts
|       |   |   |   |   |   |-- AvatarEditable.vue
|       |   |   |   |   |   |-- AvatarEditor.vue
|       |   |   |   |   |   |-- AvatarGroup.stories.ts
|       |   |   |   |   |   `-- AvatarGroup.vue
|       |   |   |   |   |-- InfiniteLoading.stories.ts
|       |   |   |   |   |-- InfiniteLoading.vue
|       |   |   |   |   |-- SourceAppBadge.stories.ts
|       |   |   |   |   `-- SourceAppBadge.vue
|       |   |   |   |-- composables/
|       |   |   |   |   |-- common/
|       |   |   |   |   |   |-- async.ts
|       |   |   |   |   |   |-- steps.ts
|       |   |   |   |   |   `-- window.ts
|       |   |   |   |   |-- form/
|       |   |   |   |   |   |-- fileUpload.ts
|       |   |   |   |   |   |-- input.ts
|       |   |   |   |   |   |-- select.ts
|       |   |   |   |   |   `-- textInput.ts
|       |   |   |   |   |-- layout/
|       |   |   |   |   |   |-- menu.ts
|       |   |   |   |   |   `-- resize.ts
|       |   |   |   |   |-- user/
|       |   |   |   |   |   `-- avatar.ts
|       |   |   |   |   `-- testing.ts
|       |   |   |   |-- directives/
|       |   |   |   |   `-- accessibility.ts
|       |   |   |   |-- helpers/
|       |   |   |   |   |-- common/
|       |   |   |   |   |   |-- components.ts
|       |   |   |   |   |   |-- error.ts
|       |   |   |   |   |   |-- ssr.ts
|       |   |   |   |   |   `-- validation.ts
|       |   |   |   |   |-- form/
|       |   |   |   |   |   |-- button.ts
|       |   |   |   |   |   |-- file.ts
|       |   |   |   |   |   `-- input.ts
|       |   |   |   |   |-- global/
|       |   |   |   |   |   |-- accessibility.ts
|       |   |   |   |   |   |-- components.ts
|       |   |   |   |   |   `-- toast.ts
|       |   |   |   |   |-- layout/
|       |   |   |   |   |   `-- components.ts
|       |   |   |   |   |-- tailwind.ts
|       |   |   |   |   `-- testing.ts
|       |   |   |   |-- stories/
|       |   |   |   |   |-- components/
|       |   |   |   |   |   |-- GlobalToast.vue
|       |   |   |   |   |   `-- SingletonManagers.vue
|       |   |   |   |   |-- composables/
|       |   |   |   |   |   `-- toast.ts
|       |   |   |   |   |-- helpers/
|       |   |   |   |   |   |-- avatar.ts
|       |   |   |   |   |   `-- storybook.ts
|       |   |   |   |   |-- styling/
|       |   |   |   |   |   |-- font/
|       |   |   |   |   |   |   |-- TextStyles.mdx
|       |   |   |   |   |   |   |-- TextStyles.stories.ts
|       |   |   |   |   |   |   `-- TextStyles.vue
|       |   |   |   |   |   `-- semantic-colors/
|       |   |   |   |   |       |-- SemanticColors.mdx
|       |   |   |   |   |       |-- SemanticColors.stories.ts
|       |   |   |   |   |       `-- SemanticColors.vue
|       |   |   |   |   `-- Introduction.mdx
|       |   |   |   |-- App.vue
|       |   |   |   |-- lib.ts
|       |   |   |   |-- main.ts
|       |   |   |   |-- v3-infinite-loading.d.ts
|       |   |   |   |-- vite-env.d.ts
|       |   |   |   |-- vue-shim.d.ts
|       |   |   |   `-- vue-tippy.d.ts
|       |   |   |-- utils/
|       |   |   |   |-- tailwind-configure.cjs
|       |   |   |   |-- tailwind-configure.d.ts
|       |   |   |   `-- tailwind-configure.js
|       |   |   |-- .npmignore
|       |   |   |-- eslint.config.mjs
|       |   |   |-- index.html
|       |   |   |-- package.json
|       |   |   |-- postcss.config.js
|       |   |   |-- README.md
|       |   |   |-- tailwind.config.cjs
|       |   |   |-- tsconfig.json
|       |   |   |-- tsconfig.node.json
|       |   |   `-- vite.config.ts
|       |   |-- ui-components-nuxt/
|       |   |   |-- eslint.config.mjs
|       |   |   |-- index.js
|       |   |   |-- package.json
|       |   |   `-- README.md
|       |   |-- viewer/
|       |   |   |-- src/
|       |   |   |   |-- helpers/
|       |   |   |   |   |-- flatten.ts
|       |   |   |   |   `-- typeHelper.ts
|       |   |   |   |-- modules/
|       |   |   |   |   |-- batching/
|       |   |   |   |   |   |-- Batch.ts
|       |   |   |   |   |   |-- Batcher.ts
|       |   |   |   |   |   |-- BatchObject.ts
|       |   |   |   |   |   |-- DrawRanges.ts
|       |   |   |   |   |   |-- InstancedBatchObject.ts
|       |   |   |   |   |   |-- InstancedMeshBatch.ts
|       |   |   |   |   |   |-- LineBatch.ts
|       |   |   |   |   |   |-- MeshBatch.ts
|       |   |   |   |   |   |-- PointBatch.ts
|       |   |   |   |   |   |-- PrimitiveBatch.ts
|       |   |   |   |   |   |-- TextBatch.ts
|       |   |   |   |   |   `-- TextBatchObject.ts
|       |   |   |   |   |-- converter/
|       |   |   |   |   |   |-- Geometry.ts
|       |   |   |   |   |   |-- MeshTriangulationHelper.js
|       |   |   |   |   |   |-- Units.js
|       |   |   |   |   |   `-- VirtualArray.ts
|       |   |   |   |   |-- extensions/
|       |   |   |   |   |   |-- controls/
|       |   |   |   |   |   |   |-- FlyControls.ts
|       |   |   |   |   |   |   |-- SmoothOrbitControls.ts
|       |   |   |   |   |   |   `-- SpeckleControls.ts
|       |   |   |   |   |   |-- measurements/
|       |   |   |   |   |   |   |-- AreaMeasurement.ts
|       |   |   |   |   |   |   |-- Measurement.ts
|       |   |   |   |   |   |   |-- MeasurementPointGizmo.ts
|       |   |   |   |   |   |   |-- MeasurementsExtension.ts
|       |   |   |   |   |   |   |-- PerpendicularMeasurement.ts
|       |   |   |   |   |   |   |-- PointMeasurement.ts
|       |   |   |   |   |   |   `-- PointToPointMeasurement.ts
|       |   |   |   |   |   |-- sections/
|       |   |   |   |   |   |   |-- SectionOutlines.ts
|       |   |   |   |   |   |   `-- SectionTool.ts
|       |   |   |   |   |   |-- CameraController.ts
|       |   |   |   |   |   |-- Controls.js
|       |   |   |   |   |   |-- DiffExtension.ts
|       |   |   |   |   |   |-- ExplodeExtension.ts
|       |   |   |   |   |   |-- Extension.ts
|       |   |   |   |   |   |-- FilteringExtension.ts
|       |   |   |   |   |   |-- HybridCameraController.ts
|       |   |   |   |   |   |-- SelectionExtension.ts
|       |   |   |   |   |   |-- TransformControls.js
|       |   |   |   |   |   `-- ViewModes.ts
|       |   |   |   |   |-- filtering/
|       |   |   |   |   |   `-- PropertyManager.ts
|       |   |   |   |   |-- input/
|       |   |   |   |   |   `-- Input.ts
|       |   |   |   |   |-- loaders/
|       |   |   |   |   |   |-- OBJ/
|       |   |   |   |   |   |   |-- ObjConverter.ts
|       |   |   |   |   |   |   |-- ObjGeometryConverter.ts
|       |   |   |   |   |   |   `-- ObjLoader.ts
|       |   |   |   |   |   |-- Speckle/
|       |   |   |   |   |   |   |-- SpeckleConverter.ts
|       |   |   |   |   |   |   |-- SpeckleGeometryConverter.ts
|       |   |   |   |   |   |   |-- SpeckleLoader.ts
|       |   |   |   |   |   |   `-- SpeckleOfflineLoader.ts
|       |   |   |   |   |   |-- GeometryConverter.ts
|       |   |   |   |   |   `-- Loader.ts
|       |   |   |   |   |-- materials/
|       |   |   |   |   |   |-- shaders/
|       |   |   |   |   |   |   |-- speckle-apply-ao-frag.ts
|       |   |   |   |   |   |   |-- speckle-apply-ao-vert.ts
|       |   |   |   |   |   |   |-- speckle-basic-frag.ts
|       |   |   |   |   |   |   |-- speckle-basic-vert.ts
|       |   |   |   |   |   |   |-- speckle-copy-output-frag.ts
|       |   |   |   |   |   |   |-- speckle-copy-output-vert.ts
|       |   |   |   |   |   |   |-- speckle-depth-frag.ts
|       |   |   |   |   |   |   |-- speckle-depth-normal-frag.ts
|       |   |   |   |   |   |   |-- speckle-depth-normal-id-frag.ts
|       |   |   |   |   |   |   |-- speckle-depth-normal-id-vert.ts
|       |   |   |   |   |   |   |-- speckle-depth-normal-vert.ts
|       |   |   |   |   |   |   |-- speckle-depth-vert.ts
|       |   |   |   |   |   |   |-- speckle-displace-frag.ts
|       |   |   |   |   |   |   |-- speckle-displace.vert.ts
|       |   |   |   |   |   |   |-- speckle-edges-generator-frag.ts
|       |   |   |   |   |   |   |-- speckle-edges-generator-vert.ts
|       |   |   |   |   |   |   |-- speckle-ghost-frag.ts
|       |   |   |   |   |   |   |-- speckle-ghost-vert.ts
|       |   |   |   |   |   |   |-- speckle-line-frag.ts
|       |   |   |   |   |   |   |-- speckle-line-vert.ts
|       |   |   |   |   |   |   |-- speckle-normal-frag.ts
|       |   |   |   |   |   |   |-- speckle-normal-vert.ts
|       |   |   |   |   |   |   |-- speckle-point-frag.ts
|       |   |   |   |   |   |   |-- speckle-point-vert.ts
|       |   |   |   |   |   |   |-- speckle-sao-frag.ts
|       |   |   |   |   |   |   |-- speckle-sao-vert.ts
|       |   |   |   |   |   |   |-- speckle-shadowcatche-frag.ts
|       |   |   |   |   |   |   |-- speckle-shadowcatcher-vert.ts
|       |   |   |   |   |   |   |-- speckle-standard-colored-frag.ts
|       |   |   |   |   |   |   |-- speckle-standard-colored-vert.ts
|       |   |   |   |   |   |   |-- speckle-standard-frag.ts
|       |   |   |   |   |   |   |-- speckle-standard-vert.ts
|       |   |   |   |   |   |   |-- speckle-static-ao-accumulate-frag.ts
|       |   |   |   |   |   |   |-- speckle-static-ao-accumulate-vert.ts
|       |   |   |   |   |   |   |-- speckle-static-ao-generate-frag.ts
|       |   |   |   |   |   |   |-- speckle-static-ao-generate-vert.ts
|       |   |   |   |   |   |   |-- speckle-temporal-supersampling-frag.ts
|       |   |   |   |   |   |   |-- speckle-temporal-supersampling-vert.ts
|       |   |   |   |   |   |   |-- speckle-text-frag.ts
|       |   |   |   |   |   |   |-- speckle-text-vert.ts
|       |   |   |   |   |   |   |-- speckle-viewport-frag.ts
|       |   |   |   |   |   |   `-- speckle-viewport-vert.ts
|       |   |   |   |   |   |-- MaterialOptions.ts
|       |   |   |   |   |   |-- Materials.ts
|       |   |   |   |   |   |-- SpeckleBasicMaterial.ts
|       |   |   |   |   |   |-- SpeckleDepthMaterial.ts
|       |   |   |   |   |   |-- SpeckleDepthNormalIdMaterial.ts
|       |   |   |   |   |   |-- SpeckleDepthNormalMaterial.ts
|       |   |   |   |   |   |-- SpeckleDisplaceMaterial.ts
|       |   |   |   |   |   |-- SpeckleGhostMaterial.ts
|       |   |   |   |   |   |-- SpeckleLineMaterial.ts
|       |   |   |   |   |   |-- SpeckleMatcapMaterial.ts
|       |   |   |   |   |   |-- SpeckleMaterial.ts
|       |   |   |   |   |   |-- SpeckleNormalMaterial.ts
|       |   |   |   |   |   |-- SpecklePointColouredMaterial.ts
|       |   |   |   |   |   |-- SpecklePointMaterial.ts
|       |   |   |   |   |   |-- SpeckleShadowcatcherMaterial.ts
|       |   |   |   |   |   |-- SpeckleStandardColoredMaterial.ts
|       |   |   |   |   |   |-- SpeckleStandardMaterial.ts
|       |   |   |   |   |   |-- SpeckleTextColoredMaterial.ts
|       |   |   |   |   |   |-- SpeckleTextMaterial.ts
|       |   |   |   |   |   `-- SpeckleViewportMaterial.ts
|       |   |   |   |   |-- objects/
|       |   |   |   |   |   |-- AccelerationStructure.ts
|       |   |   |   |   |   |-- ExtendedInstancedMesh.ts
|       |   |   |   |   |   |-- JitterQuad.ts
|       |   |   |   |   |   |-- RotatablePMREMGenerator.ts
|       |   |   |   |   |   |-- SpeckleBatchedText.ts
|       |   |   |   |   |   |-- SpeckleCamera.ts
|       |   |   |   |   |   |-- SpeckleInstancedMesh.ts
|       |   |   |   |   |   |-- SpeckleMesh.ts
|       |   |   |   |   |   |-- SpeckleRaycaster.ts
|       |   |   |   |   |   |-- SpeckleWebGLRenderer.ts
|       |   |   |   |   |   |-- TextLabel.ts
|       |   |   |   |   |   `-- TopLevelAccelerationStructure.ts
|       |   |   |   |   |-- pipeline/
|       |   |   |   |   |   |-- Passes/
|       |   |   |   |   |   |   |-- BlendPass.ts
|       |   |   |   |   |   |   |-- DepthNormalIdPass.ts
|       |   |   |   |   |   |   |-- DepthNormalPass.ts
|       |   |   |   |   |   |   |-- DepthPass.ts
|       |   |   |   |   |   |   |-- EdgesPass.ts
|       |   |   |   |   |   |   |-- GeometryPass.ts
|       |   |   |   |   |   |   |-- GPass.ts
|       |   |   |   |   |   |   |-- NormalsPass.ts
|       |   |   |   |   |   |   |-- OutputPass.ts
|       |   |   |   |   |   |   |-- ProgressiveAOPass.ts
|       |   |   |   |   |   |   |-- ShadedPass.ts
|       |   |   |   |   |   |   |-- ShadowcatcherPass.ts
|       |   |   |   |   |   |   |-- StencilMaskPass.ts
|       |   |   |   |   |   |   |-- StencilPass.ts
|       |   |   |   |   |   |   |-- TAAPass.ts
|       |   |   |   |   |   |   `-- ViewportPass.ts
|       |   |   |   |   |   `-- Pipelines/
|       |   |   |   |   |       |-- ArcticViewPipeline.ts
|       |   |   |   |   |       |-- DefaultPipeline.ts
|       |   |   |   |   |       |-- EdgesPipeline.ts
|       |   |   |   |   |       |-- PenViewPipeline.ts
|       |   |   |   |   |       |-- Pipeline.ts
|       |   |   |   |   |       |-- ProgressivePipeline.ts
|       |   |   |   |   |       |-- ShadedViewPipeline.ts
|       |   |   |   |   |       |-- SolidViewPipeline.ts
|       |   |   |   |   |       `-- TAAPipeline.ts
|       |   |   |   |   |-- queries/
|       |   |   |   |   |   |-- IntersectionQuerySolver.ts
|       |   |   |   |   |   |-- PointQuerySolver.ts
|       |   |   |   |   |   |-- Queries.ts
|       |   |   |   |   |   `-- Query.ts
|       |   |   |   |   |-- three/
|       |   |   |   |   |   `-- stats.ts
|       |   |   |   |   |-- tree/
|       |   |   |   |   |   |-- NodeMap.ts
|       |   |   |   |   |   |-- NodeRenderView.ts
|       |   |   |   |   |   |-- RenderTree.ts
|       |   |   |   |   |   `-- WorldTree.ts
|       |   |   |   |   |-- utils/
|       |   |   |   |   |   |-- AngleDamper.ts
|       |   |   |   |   |   |-- Damper.ts
|       |   |   |   |   |   `-- Logger.ts
|       |   |   |   |   |-- Assets.ts
|       |   |   |   |   |-- EventEmitter.ts
|       |   |   |   |   |-- Helpers.ts
|       |   |   |   |   |-- Intersections.ts
|       |   |   |   |   |-- LegacyViewer.ts
|       |   |   |   |   |-- Shadowcatcher.ts
|       |   |   |   |   |-- ShadowcatcherConfig.ts
|       |   |   |   |   |-- SpeckleRenderer.ts
|       |   |   |   |   |-- UrlHelper.ts
|       |   |   |   |   |-- Utils.ts
|       |   |   |   |   |-- Viewer.ts
|       |   |   |   |   |-- WebXrViewer.ts
|       |   |   |   |   `-- World.ts
|       |   |   |   |-- type-augmentations/
|       |   |   |   |   |-- files.d.ts
|       |   |   |   |   |-- three-extensions.ts
|       |   |   |   |   |-- three.d.ts
|       |   |   |   |   `-- troika-three-text.d.ts
|       |   |   |   |-- index.ts
|       |   |   |   `-- IViewer.ts
|       |   |   |-- test/
|       |   |   |   |-- __snapshots__/
|       |   |   |   |   `-- draw-ranges.test.ts.snap
|       |   |   |   `-- draw-ranges.test.ts
|       |   |   |-- .babelrc
|       |   |   |-- .gitignore
|       |   |   |-- eslint.config.mjs
|       |   |   |-- package.json
|       |   |   |-- readme.md
|       |   |   |-- rollup.config.js
|       |   |   |-- sample-objects.txt
|       |   |   |-- tsconfig.build.json
|       |   |   |-- tsconfig.eslint.json
|       |   |   |-- tsconfig.json
|       |   |   |-- vite.config.ts
|       |   |   `-- vitest.config.js
|       |   |-- viewer-sandbox/
|       |   |   |-- src/
|       |   |   |   |-- Extensions/
|       |   |   |   |   |-- SectionCaps.ts/
|       |   |   |   |   |   |-- SectionCaps.ts
|       |   |   |   |   |   |-- SectionCapsPipeline.ts
|       |   |   |   |   |   |-- StencilBackPass.ts
|       |   |   |   |   |   `-- StencilFrontPass.ts
|       |   |   |   |   |-- BoxSelection.ts
|       |   |   |   |   |-- CameraPlanes.ts
|       |   |   |   |   |-- ExtendedSelection.ts
|       |   |   |   |   |-- PassReader.ts
|       |   |   |   |   |-- RotateCamera.ts
|       |   |   |   |   `-- XrExtension.ts
|       |   |   |   |-- Pipelines/
|       |   |   |   |   `-- Snow/
|       |   |   |   |       |-- objectSnowFrag.ts
|       |   |   |   |       |-- objectSnowVert.ts
|       |   |   |   |       |-- snowfallFrag.ts
|       |   |   |   |       |-- SnowFallPass.ts
|       |   |   |   |       |-- snowfallVert.ts
|       |   |   |   |       |-- SnowMaterial.ts
|       |   |   |   |       `-- SnowPipeline.ts
|       |   |   |   |-- type-augmentations/
|       |   |   |   |   `-- vite-env.d.ts
|       |   |   |   |-- JSONSpeckleStream.ts
|       |   |   |   |-- main-multi.ts
|       |   |   |   |-- main.ts
|       |   |   |   |-- Sandbox.ts
|       |   |   |   `-- style.css
|       |   |   |-- .gitignore
|       |   |   |-- eslint.config.mjs
|       |   |   |-- favicon.svg
|       |   |   |-- index.html
|       |   |   |-- package.json
|       |   |   |-- readme.md
|       |   |   |-- sample-hdri.exr
|       |   |   |-- tsconfig.json
|       |   |   `-- vite.config.js
|       |   `-- webhook-service/
|       |       |-- src/
|       |       |   |-- observability/
|       |       |   |   |-- logging.js
|       |       |   |   `-- prometheusMetrics.js
|       |       |   |-- errors.js
|       |       |   |-- knex.js
|       |       |   |-- main.js
|       |       |   `-- webhookCaller.js
|       |       |-- Dockerfile
|       |       |-- eslint.config.mjs
|       |       |-- jsconfig.json
|       |       `-- package.json
|       |-- setup/
|       |   |-- db/
|       |   |   |-- 10-docker_postgres_init.sql
|       |   |   `-- 11-docker_postgres_keycloak_init.sql
|       |   `-- keycloak/
|       |       |-- speckle-realm.json
|       |       `-- speckle-users-0.json
|       |-- test-queries/
|       |   |-- all-tables-sizes.sql
|       |   |-- closure-fullcount.sql
|       |   |-- closure-simple-fast.sql
|       |   |-- closure-simple-slow.sql
|       |   |-- closure-two-stage.sql
|       |   |-- materialised-fullcount.sql
|       |   |-- materialised-simple-ordinality.sql
|       |   |-- materialised-simple.sql
|       |   `-- objects-sizes.sql
|       |-- test_data/
|       |   |-- root_data.json
|       |   |-- steel_column_obsolete_project.json
|       |   |-- steel_column_precon.json
|       |   |-- timber_column_data.json
|       |   `-- timber_column_data_2.json
|       |-- tests/
|       |   `-- deployment/
|       |       |-- docker-compose/
|       |       |   |-- docker-compose-shell.nix
|       |       |   |-- docker-compose-speckle.override.yml
|       |       |   |-- docker-compose-test.override.yml
|       |       |   `-- Tiltfile
|       |       |-- helm/
|       |       |   |-- manifests/
|       |       |   |   |-- coredns.configmap.yaml
|       |       |   |   |-- ingress-nginx.namespace.yaml
|       |       |   |   |-- minio.namespace.yaml
|       |       |   |   |-- minio.pv.yaml
|       |       |   |   |-- minio.pvc.yaml
|       |       |   |   |-- postgres.namespace.yaml
|       |       |   |   |-- postgres.pv.yaml
|       |       |   |   |-- postgres.pvc.yaml
|       |       |   |   |-- priorityclass.yaml
|       |       |   |   |-- prometheus.namespace.yaml
|       |       |   |   |-- speckle-server.namespace.yaml
|       |       |   |   |-- speckle-server.secret.yaml
|       |       |   |   `-- valkey.namespace.yaml
|       |       |   |-- scripts/
|       |       |   |   `-- coredns-up.sh
|       |       |   |-- values/
|       |       |   |   |-- minio.values.yaml
|       |       |   |   |-- nginx.values.yaml
|       |       |   |   |-- postgres.values.yaml
|       |       |   |   |-- prometheus-operator-crds.values.yaml
|       |       |   |   |-- speckle-server.values.yaml
|       |       |   |   `-- valkey.values.yaml
|       |       |   |-- cluster-config.yaml
|       |       |   |-- helm-chart-shell.nix
|       |       |   `-- Tiltfile
|       |       |-- build-images.tiltfile
|       |       `-- load-images.tiltfile
|       |-- utils/
|       |   |-- 1click_image_scripts/
|       |   |   `-- setup.py
|       |   |-- docker-compose-ingress/
|       |   |   |-- nginx/
|       |   |   |   |-- conf/
|       |   |   |   |   `-- mime.types
|       |   |   |   |-- templates/
|       |   |   |   |   `-- nginx.conf.template
|       |   |   |   `-- default.conf
|       |   |   `-- Dockerfile
|       |   |-- helm/
|       |   |   |-- speckle-server/
|       |   |   |   |-- templates/
|       |   |   |   |   |-- fileimport_service/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- networkpolicy.cilium.yml
|       |   |   |   |   |   |-- networkpolicy.kubernetes.yml
|       |   |   |   |   |   |-- service.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- frontend_2/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- networkpolicy.cilium.yml
|       |   |   |   |   |   |-- networkpolicy.kubernetes.yml
|       |   |   |   |   |   |-- service.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- ifc_import_service/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- configmap-db-certificate.yml
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- service.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- monitoring/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- networkpolicy.cilium.yml
|       |   |   |   |   |   |-- networkpolicy.kubernetes.yml
|       |   |   |   |   |   |-- service.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- objects/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- networkpolicy.cilium.yml
|       |   |   |   |   |   |-- networkpolicy.kubernetes.yml
|       |   |   |   |   |   |-- service.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- preview_service/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- hpa.yaml
|       |   |   |   |   |   |-- networkpolicy.cilium.yml
|       |   |   |   |   |   |-- networkpolicy.kubernetes.yml
|       |   |   |   |   |   |-- service.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- server/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- networkpolicy.cilium.yml
|       |   |   |   |   |   |-- networkpolicy.kubernetes.yml
|       |   |   |   |   |   |-- service.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- tests/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- networkpolicy.cilium.yml
|       |   |   |   |   |   |-- networkpolicy.kubernetes.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- webhook_service/
|       |   |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |   |-- deployment.yml
|       |   |   |   |   |   |-- networkpolicy.cilium.yml
|       |   |   |   |   |   |-- networkpolicy.kubernetes.yml
|       |   |   |   |   |   |-- service.yml
|       |   |   |   |   |   `-- serviceaccount.yml
|       |   |   |   |   |-- _helpers.tpl
|       |   |   |   |   |-- configmap-db-certificate.yml
|       |   |   |   |   |-- file.minion.ingress.yml
|       |   |   |   |   |-- master.ingress.yml
|       |   |   |   |   |-- minion.ingress.yml
|       |   |   |   |   |-- namespace.yml
|       |   |   |   |   |-- objects.minion.ingress.yml
|       |   |   |   |   |-- redirect.ingress.yml
|       |   |   |   |   `-- servicemonitor.yml
|       |   |   |   |-- .helmignore
|       |   |   |   |-- all-resources.yaml
|       |   |   |   |-- apply-ingress.ps1
|       |   |   |   |-- Chart.yaml
|       |   |   |   |-- ingress-and-service-fix.yaml
|       |   |   |   |-- ingress-backup.yaml
|       |   |   |   |-- ingress-extracted.yaml
|       |   |   |   |-- ingress-only-clean.yaml
|       |   |   |   |-- ingress-only.yaml
|       |   |   |   |-- ingress-resources.yaml
|       |   |   |   |-- ingress-temp.yaml
|       |   |   |   |-- minion-ingress-current.yaml
|       |   |   |   |-- minion-ingress.yaml
|       |   |   |   |-- objects-ingress-current.yaml
|       |   |   |   |-- schematic.md
|       |   |   |   |-- values.schema.json
|       |   |   |   `-- values.yaml
|       |   |   |-- .helm-readme-configuration.json
|       |   |   `-- update-schema-json.sh
|       |   |-- postgres/
|       |   |   `-- Dockerfile
|       |   |-- test-deployment/
|       |   |   |-- Dockerfile
|       |   |   |-- install_prerequisites.sh
|       |   |   |-- requirements.txt
|       |   |   `-- run_tests.py
|       |   |-- ubuntu-chromium/
|       |   |   `-- Dockerfile
|       |   |-- dev-all.js
|       |   |-- ensure-tailwind-deps.mjs
|       |   |-- eslint-projectwide.mjs
|       |   `-- tee.js
|       |-- .dockerignore
|       |-- .editorconfig
|       |-- .gitguardian.yml
|       |-- .gitignore
|       |-- .graphqlrc
|       |-- .pre-commit-config.yaml
|       |-- .prettierignore
|       |-- .prettierrc
|       |-- .yarnrc.yml
|       |-- AWS_VIEWER_FIX_SUMMARY.md
|       |-- CONTRIBUTING.md
|       |-- current-policy-ascii.json
|       |-- current-policy.json
|       |-- current-values-fixed.yaml
|       |-- current-values.yaml
|       |-- deployments-backup.yaml
|       |-- DISTRIBUTION_GUIDE.md
|       |-- docker-compose-deps.yml
|       |-- docker-compose-ingress.yml
|       |-- docker-compose-speckle.yml
|       |-- docker-compose-test.yml
|       |-- eslint.config.mjs
|       |-- graphql.txt
|       |-- ingress-backup.yaml
|       |-- ingress-resources.yaml
|       |-- ingress-values.yaml
|       |-- LICENSE
|       |-- lint-staged.config.js
|       |-- mise.toml
|       |-- package.json
|       |-- rds-ca-bundle.pem
|       |-- README.md
|       |-- SECURITY.md
|       |-- tsconfig.json
|       |-- vitest.workspace.mjs
|       `-- workspace.code-workspace
|-- .gitignore
`-- Architecture.md
```
