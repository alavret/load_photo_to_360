$ldapFilter = "(memberOf=CN=Yandex360,OU=Groups,OU=Office,DC=yandry,DC=ru)"
$searchRoot = "DC=yandry,DC=ru"
$OutputPath = 'c:\Temp\Photos\Download'
Function ConvertTo-Jpeg {
    param ($userName,$photoAsBytes,$path='c:\temp')
    if ( ! ( Test-Path $path ) ) { New-Item $path -ItemType Directory }
    $Filename=Join-Path -Path $path -ChildPath "$($userName).jpg"
    [System.Io.File]::WriteAllBytes( $Filename,$photoAsBytes )
}
 
 #Import-Module ActiveDirectory
 $Users = Get-ADUser -LDAPFilter $ldapFilter -SearchBase $searchRoot  -Properties thumbnailPhoto, mail | ? { ($_.thumbnailPhoto) }
 ForEach ( $User in $Users ) { 
     Write-Warning "Write file for $($user.mail.Split("@")[0])." 
     ConvertTo-Jpeg -userName $user.mail.Split("@")[0] -photoAsBytes $user.thumbnailPhoto -path $OutputPath
 }
