{{/*
Expand the name of the chart.
*/}}
{{- define "uac.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "uac.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "uac.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "uac.labels" -}}
helm.sh/chart: {{ include "uac.chart" . }}
{{ include "uac.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "uac.selectorLabels" -}}
app.kubernetes.io/name: {{ include "uac.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "uac.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "uac.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database host
*/}}
{{- define "uac.databaseHost" -}}
{{- if .Values.externalDatabase.enabled }}
{{- .Values.externalDatabase.host }}
{{- else }}
{{- printf "%s-postgresql" .Release.Name }}
{{- end }}
{{- end }}

{{/*
Database port
*/}}
{{- define "uac.databasePort" -}}
{{- if .Values.externalDatabase.enabled }}
{{- .Values.externalDatabase.port }}
{{- else }}
{{- 5432 }}
{{- end }}
{{- end }}

{{/*
Database name
*/}}
{{- define "uac.databaseName" -}}
{{- if .Values.externalDatabase.enabled }}
{{- .Values.externalDatabase.database }}
{{- else }}
{{- .Values.postgresql.auth.database }}
{{- end }}
{{- end }}

{{/*
Database user
*/}}
{{- define "uac.databaseUser" -}}
{{- if .Values.externalDatabase.enabled }}
{{- .Values.externalDatabase.user }}
{{- else }}
{{- .Values.postgresql.auth.username }}
{{- end }}
{{- end }}
