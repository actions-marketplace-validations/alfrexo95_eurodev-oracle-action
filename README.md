# 🇪🇺 EuroDev Oracle Action

Automated GDPR compliance checks and EU tech facts for European developers.

## Usage
```yaml
- uses: alfrexo95/eurodev-oracle-action@v1.0.0
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    etherscan-api-key: ${{ secrets.ETHERSCAN_API_KEY }}
    crypto-address-eth: ${{ secrets.CRYPTO_ADDRESS_ETH }}
```
