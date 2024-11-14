$ldapFilter = "(memberOf=CN=Yandex360,OU=Groups,OU=Office,DC=yandry,DC=ru)"
$searchRoot = "DC=yandry,DC=ru"
$usersWithoutImage = Get-ADUser -LDAPFilter $ldapFilter -SearchBase $searchRoot -properties thumbnailPhoto, mail | ? {(-not($_.thumbnailPhoto))}
$InputPath = 'c:\Temp\Photos\input'
$ImageExtention = ".jpg"

if ( Test-Path $InputPath )  {
    $repPics = (Get-childItem $InputPath).basename
    Write-host "Found $($usersWithoutImage.Count) users without a photo."
    ForEach ($user in $usersWithoutImage){
        $alias = $user.mail.Split("@")[0]
        if ($repPics -contains $alias){
            Write-host "Users name [$alias] is in the users photo directory, uploading..."
            $imagePath = Join-Path -Path $InputPath -ChildPath "$($alias)$($ImageExtention)"
            $ADphoto = [byte[]](Get-Content $imagePath -Encoding byte)
            Set-ADUser $user -Replace @{thumbnailPhoto=$ADphoto}
        }
        else{
            Write-Warning "Users name [$alias] is NOT in the users photo directory, please update!"
        }
    }
}
else {
    Write-host "Path $($InputPath) not exist. Exit."
}