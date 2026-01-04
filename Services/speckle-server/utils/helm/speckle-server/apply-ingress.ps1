# Extract and apply ingress resources from Helm template
Write-Host "Rendering Helm templates..."
helm template speckle-server . --namespace speckle-production --values C:\Users\shine\speckle1\speckle-server\infrastructure\helm-values-aws.yaml > all-resources.yaml

Write-Host "Extracting ingress resources..."
# Read the file and extract ingress resources
$content = Get-Content all-resources.yaml -Raw
$docs = $content -split '(?=^---)'
$ingressDocs = @()

foreach ($doc in $docs) {
    if ($doc -match 'kind:\s+Ingress' -and $doc -match 'speckle-server-minion') {
        $ingressDocs += $doc
    }
}

if ($ingressDocs.Count -gt 0) {
    $ingressDocs -join "`n---`n" | Out-File -Encoding utf8 ingress-to-apply.yaml
    Write-Host "Found $($ingressDocs.Count) ingress resources"
    Write-Host "Applying ingress resources..."
    kubectl apply -f ingress-to-apply.yaml
    Write-Host "Done!"
} else {
    Write-Host "No ingress resources found"
}



